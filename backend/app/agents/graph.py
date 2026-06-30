import json
import logging
import time
from typing import Awaitable, Callable, Literal, TypeVar

from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.company_summary import enrich_company_research
from app.agents.retry import invoke_llm
from app.agents.validation import guard_tailored_content
from app.core.pipeline_logging import log_pipeline_event, log_pipeline_step
from app.services.webhook import dispatch_pipeline_webhook, get_stored_webhook_url
from app.models.cover_letter import CoverLetterDocument
from app.models.resume import AgentRun, ATSScore, ResumeDocument
from app.models.job_intelligence import InboxJob
from app.schemas.resume_content import CoverLetterContent, ResumeContent, resume_to_text
from app.scrapers.company_researcher import research_company
from app.services.ats.persist import save_ats_score
from app.services.llm.client import create_chat_model, get_user_llm_config
from app.services.rag.ingest import ingest_resume_content, ingest_text, search_chunks
from app.services.resume.renderer import render_resume_latex
from app.sockets.chat import sio

logger = logging.getLogger(__name__)

PipelineMode = Literal["full", "tailor_only", "cover_letter_only"]
T = TypeVar("T")


class PipelineState(dict):
    """Typed-ish pipeline state bag."""


async def _emit(resume_id: str, event: str, data: dict) -> None:
    await sio.emit(event, data, room=f"resume:{resume_id}")


async def _run_step(
    db: AsyncSession,
    resume_id,
    agent_type: str,
    status: str,
    steps: dict | None = None,
    error: str | None = None,
) -> None:
    run = AgentRun(resume_id=resume_id, agent_type=agent_type, status=status, steps_json=steps, error=error)
    db.add(run)
    await db.flush()


async def _fail_step(db: AsyncSession, resume_id, step: str, error: str) -> None:
    await _run_step(db, resume_id, step, "failed", error=error)
    await _emit(resume_id, "agent_step", {"step": step, "status": "failed", "error": error})


async def _run_timed_step(
    resume_id: str,
    step: str,
    runner: Callable[[], Awaitable[T]],
) -> T:
    started = time.perf_counter()
    try:
        result = await runner()
    except Exception:
        duration_ms = int((time.perf_counter() - started) * 1000)
        log_pipeline_step(logger, resume_id=resume_id, step=step, duration_ms=duration_ms, status="failed")
        raise
    duration_ms = int((time.perf_counter() - started) * 1000)
    log_pipeline_step(logger, resume_id=resume_id, step=step, duration_ms=duration_ms, status="completed")
    return result


def _cache_key_jd(jd: str) -> str:
    return jd[:500]


def _should_reuse_analysis(insights: dict, job_description: str, company_url: str | None) -> bool:
    if insights.get("_cached_jd") != _cache_key_jd(job_description or ""):
        return False
    if (insights.get("_cached_company_url") or "") != (company_url or ""):
        return False
    return bool(insights.get("jd_analysis"))


async def ingest_context(state: PipelineState, db: AsyncSession) -> PipelineState:
    resume_id = state["resume_id"]
    await _emit(resume_id, "agent_step", {"step": "ingest_context", "status": "running"})
    llm_config = await get_user_llm_config(db, state["user_id"])

    if llm_config and state.get("job_description"):
        await ingest_text(db, state["user_id"], "job_description", resume_id, state["job_description"], llm_config)

    if llm_config and state.get("source_type") == "upload" and state.get("source_content"):
        await ingest_resume_content(
            db,
            state["user_id"],
            state["source_content"],
            llm_config,
            source_id=resume_id,
        )

    await _run_step(db, resume_id, "ingest_context", "completed")
    await _emit(resume_id, "agent_step", {"step": "ingest_context", "status": "completed"})
    return state


async def analyze_jd(state: PipelineState, db: AsyncSession) -> PipelineState:
    resume_id = state["resume_id"]
    await _emit(resume_id, "agent_step", {"step": "analyze_jd", "status": "running"})
    llm_config = await get_user_llm_config(db, state["user_id"])
    jd = state.get("job_description", "")

    if not jd:
        state["jd_analysis"] = {"sections": [], "keywords": [], "required_skills": [], "warning": "No job description provided."}
    elif not llm_config:
        state["jd_analysis"] = {
            "sections": [],
            "keywords": [],
            "required_skills": [],
            "warning": "No API key — JD analysis skipped.",
        }
    else:
        llm = create_chat_model(llm_config)
        prompt = f"""Analyze this job description and return JSON with keys:
- required_skills: list of strings
- responsibilities: list of strings
- seniority: string
- keywords: list of important ATS keywords

Target title: {state.get("job_title") or ""}
Target company: {state.get("company_name") or ""}

Job Description:
{jd[:6000]}"""
        try:
            res = await invoke_llm(
                llm,
                [SystemMessage(content="Return valid JSON only."), HumanMessage(content=prompt)],
            )
            parsed = json.loads(res.content if isinstance(res.content, str) else str(res.content))
            state["jd_analysis"] = parsed
        except Exception as e:
            logger.warning("JD analysis failed: %s", e)
            state["jd_analysis"] = {"keywords": [], "required_skills": [], "responsibilities": [], "error": str(e)}

    await _run_step(db, resume_id, "analyze_jd", "completed", state["jd_analysis"])
    await _emit(resume_id, "agent_step", {"step": "analyze_jd", "status": "completed", "data": state["jd_analysis"]})
    return state


async def research_company_step(state: PipelineState, db: AsyncSession, *, reuse: bool = False) -> PipelineState:
    resume_id = state["resume_id"]
    url = state.get("company_url")

    if reuse and state.get("company_research"):
        await _emit(resume_id, "agent_step", {"step": "research_company", "status": "completed", "cached": True})
        return state

    if not url:
        state["company_research"] = {"company_name": state.get("company_name")} if state.get("company_name") else {}
        await _run_step(db, resume_id, "research_company", "completed", {"skipped": True})
        await _emit(resume_id, "agent_step", {"step": "research_company", "status": "completed", "skipped": True})
        return state

    await _emit(resume_id, "agent_step", {"step": "research_company", "status": "running"})
    try:
        research = await research_company(url)
        llm_config = await get_user_llm_config(db, state["user_id"])
        research = await enrich_company_research(research, llm_config)
        state["company_research"] = research
        if llm_config and research.get("raw_text"):
            await ingest_text(db, state["user_id"], "company", resume_id, research["raw_text"], llm_config)
    except Exception as e:
        logger.warning("Company research failed: %s", e)
        state["company_research"] = {"error": str(e)}

    await _run_step(db, resume_id, "research_company", "completed", state.get("company_research"))
    await _emit(resume_id, "agent_step", {"step": "research_company", "status": "completed"})
    return state


async def tailor_resume(state: PipelineState, db: AsyncSession) -> PipelineState:
    resume_id = state["resume_id"]
    await _emit(resume_id, "agent_step", {"step": "tailor_resume", "status": "running"})
    llm_config = await get_user_llm_config(db, state["user_id"])
    source_content = state.get("source_content") or state.get("content") or {}
    content = ResumeContent.model_validate(source_content)

    if not llm_config:
        state["content"] = content.model_dump()
        state["tailoring_insights"] = ["No API key configured — using profile as-is."]
        await _run_step(db, resume_id, "tailor_resume", "completed")
        await _emit(resume_id, "agent_step", {"step": "tailor_resume", "status": "completed"})
        return state

    llm = create_chat_model(llm_config)
    chunks = await search_chunks(db, state["user_id"], state.get("job_description", ""), llm_config)
    rag_context = "\n---\n".join(c.chunk_text for c in chunks[:6])
    jd_analysis = state.get("jd_analysis") or {}
    jd = json.dumps(jd_analysis)
    company = state.get("company_research", {}).get("summary", "")

    ats_keywords = ", ".join(str(k) for k in (jd_analysis.get("keywords") or [])[:25])
    required_skills = ", ".join(str(s) for s in (jd_analysis.get("required_skills") or [])[:20])

    prompt = f"""You are an expert ATS-optimized resume writer. Tailor the resume JSON for the target job.

STRICT RULES:
1. Return ONLY valid JSON matching the exact same schema as the input.
2. Preserve every factual claim, employer, job title, date, degree, project name, and metric exactly.
3. Do NOT invent skills, tools, certifications, companies, projects, or accomplishments absent from the source.
4. Naturally weave the ATS keywords below into bullets and summary (no keyword stuffing).
5. Reorder bullets within each experience entry so the most job-relevant accomplishments appear first.
6. Write the summary to directly address the role's core requirements using the candidate's real experience.
7. Use strong action verbs and preserve existing numeric metrics in bullets.

ATS KEYWORDS TO INCORPORATE NATURALLY:
{ats_keywords or "(see JD analysis)"}

REQUIRED SKILLS TO HIGHLIGHT:
{required_skills or "(see JD analysis)"}

Current resume JSON:
{content.model_dump_json()}

JD analysis: {jd}
Target title: {state.get("job_title") or ""}
Target company: {state.get("company_name") or ""}
Company context: {company}
RAG context: {rag_context[:3000]}"""

    insights = ["Aligned experience bullets with job requirements", "Incorporated ATS keywords naturally into content", "Optimized summary and skills for target role"]

    try:
        res = await invoke_llm(
            llm,
            [
                SystemMessage(content="You are an expert resume writer. Return only JSON."),
                HumanMessage(content=prompt),
            ],
        )
        raw = res.content if isinstance(res.content, str) else str(res.content)
        tailored = json.loads(raw)
        validated = ResumeContent.model_validate(tailored).model_dump()
        cleaned, guard_warnings = guard_tailored_content(source_content, validated)
        state["content"] = cleaned
        state["tailoring_insights"] = insights + guard_warnings
    except Exception as e:
        logger.warning("Resume tailoring failed: %s", e)
        state["content"] = content.model_dump()
        state["tailoring_insights"] = [f"Tailoring skipped: {e}"]

    await _run_step(db, resume_id, "tailor_resume", "completed")
    await _emit(resume_id, "agent_step", {"step": "tailor_resume", "status": "completed"})
    return state


async def generate_cover_letter(state: PipelineState, db: AsyncSession) -> PipelineState:
    if not state.get("create_cover_letter"):
        return state

    resume_id = state["resume_id"]
    await _emit(resume_id, "agent_step", {"step": "cover_letter", "status": "running"})
    llm_config = await get_user_llm_config(db, state["user_id"])
    meta = state.get("cover_letter_meta") or {}
    company = state.get("company_research") or {}
    content = CoverLetterContent(
        recipient_name=meta.get("hiring_manager_name", ""),
        company_name=company.get("company_name") or state.get("company_name", ""),
        company_address=", ".join(filter(None, [meta.get("street_address"), meta.get("city"), meta.get("state_province"), meta.get("postal_code")])),
        date=meta.get("letter_date", ""),
        salutation=f"Dear {meta.get('hiring_manager_name') or 'Hiring Manager'},",
    )

    if llm_config:
        from app.services.cover_letter.generator import build_cover_letter_prompt, parse_cover_letter_response

        llm = create_chat_model(llm_config, temperature=0.5)
        resume_text = resume_to_text(ResumeContent.model_validate(state["content"]))
        prompt = build_cover_letter_prompt(
            meta=meta,
            company=company,
            jd_analysis=state.get("jd_analysis") or {},
            job_description=state.get("job_description", ""),
            resume_text=resume_text,
        )
        try:
            res = await invoke_llm(
                llm,
                [SystemMessage(content="Return valid JSON only."), HumanMessage(content=prompt)],
            )
            parsed = json.loads(res.content if isinstance(res.content, str) else str(res.content))
            content.paragraphs, content.closing = parse_cover_letter_response(parsed)
        except Exception as e:
            logger.warning("Cover letter generation failed: %s", e)
            content.paragraphs = ["I am excited to apply for this role and believe my experience is a strong fit."]

    state["cover_letter_content"] = content.model_dump()
    await _run_step(db, resume_id, "cover_letter", "completed")
    await _emit(resume_id, "agent_step", {"step": "cover_letter", "status": "completed"})
    return state


async def score_ats(state: PipelineState, db: AsyncSession) -> PipelineState:
    from app.services.ats.scorer import score_resume

    resume_id = state["resume_id"]
    await _emit(resume_id, "agent_step", {"step": "ats_score", "status": "running"})

    result = score_resume(
        state.get("content") or {},
        state.get("job_description", ""),
        state.get("jd_analysis") or {},
    )
    state["ats_result"] = result.to_dict()

    await _run_step(db, resume_id, "ats_score", "completed", state["ats_result"])
    await _emit(resume_id, "agent_step", {"step": "ats_score", "status": "completed", "data": state["ats_result"]})
    return state


async def _persist_cover_letter(db: AsyncSession, resume: ResumeDocument, content: dict) -> None:
    from app.services.resume.renderer import render_cover_letter_latex

    meta = resume.cover_letter_meta or {}
    contact = (resume.content_json or {}).get("contact", {})
    latex = render_cover_letter_latex(content, contact)
    existing = await db.execute(select(CoverLetterDocument).where(CoverLetterDocument.resume_id == resume.id))
    cl = existing.scalar_one_or_none()
    if cl:
        cl.content_json = content
        cl.latex_source = latex
        cl.status = "completed"
        return

    db.add(
        CoverLetterDocument(
            user_id=resume.user_id,
            resume_id=resume.id,
            title=f"{resume.title} — Cover Letter",
            status="completed",
            hiring_manager_name=meta.get("hiring_manager_name"),
            hiring_manager_email=meta.get("hiring_manager_email"),
            street_address=meta.get("street_address"),
            city=meta.get("city"),
            state_province=meta.get("state_province"),
            postal_code=meta.get("postal_code"),
            letter_date=meta.get("letter_date"),
            additional_context=meta.get("additional_context"),
            content_json=content,
            latex_source=latex,
        )
    )


async def _persist_ats(db: AsyncSession, resume: ResumeDocument, user_id) -> None:
    await save_ats_score(db, resume, user_id, enrich_llm=True)


async def run_generation_pipeline(
    db: AsyncSession,
    resume: ResumeDocument,
    mode: PipelineMode = "full",
) -> None:
    insights = dict(resume.insights_json or {})
    source_content = insights.get("source_content") or resume.content_json or {}
    reuse_analysis = _should_reuse_analysis(insights, resume.job_description or "", resume.company_url)

    state: PipelineState = PipelineState(
        resume_id=str(resume.id),
        user_id=str(resume.user_id),
        job_description=resume.job_description or "",
        company_url=resume.company_url,
        company_name=resume.company_name,
        job_title=insights.get("job_title"),
        create_cover_letter=resume.create_cover_letter,
        cover_letter_meta=resume.cover_letter_meta or {},
        content=resume.content_json or {},
        source_content=source_content,
        source_type=resume.source_type,
        mode=mode,
        jd_analysis=insights.get("jd_analysis", {}) if reuse_analysis else {},
        company_research=insights.get("company_research", {}) if reuse_analysis else {},
    )

    current_step = "pipeline"
    resume_id = str(resume.id)
    log_pipeline_event(logger, resume_id=resume_id, event="start", status="running", mode=mode)

    try:
        resume.status = "processing"
        insights.pop("pipeline_error", None)
        resume.insights_json = insights
        await db.commit()

        if mode == "cover_letter_only":
            state["jd_analysis"] = insights.get("jd_analysis", {})
            state["company_research"] = insights.get("company_research", {})
            current_step = "cover_letter"
            state = await _run_timed_step(resume_id, current_step, lambda: generate_cover_letter(state, db))
        elif mode == "tailor_only":
            state["jd_analysis"] = insights.get("jd_analysis", {})
            state["company_research"] = insights.get("company_research", {})
            current_step = "tailor_resume"
            state = await _run_timed_step(resume_id, current_step, lambda: tailor_resume(state, db))
            current_step = "ats_score"
            state = await _run_timed_step(resume_id, current_step, lambda: score_ats(state, db))
        else:
            current_step = "ingest_context"
            state = await _run_timed_step(resume_id, current_step, lambda: ingest_context(state, db))

            if reuse_analysis and state.get("jd_analysis"):
                await _emit(resume_id, "agent_step", {"step": "analyze_jd", "status": "completed", "cached": True})
                log_pipeline_step(
                    logger,
                    resume_id=resume_id,
                    step="analyze_jd",
                    duration_ms=0,
                    status="cached",
                )
            else:
                current_step = "analyze_jd"
                state = await _run_timed_step(resume_id, current_step, lambda: analyze_jd(state, db))

            current_step = "research_company"
            state = await _run_timed_step(
                resume_id,
                current_step,
                lambda: research_company_step(state, db, reuse=reuse_analysis and bool(state.get("company_research"))),
            )

            current_step = "tailor_resume"
            state = await _run_timed_step(resume_id, current_step, lambda: tailor_resume(state, db))

            if state.get("create_cover_letter"):
                current_step = "cover_letter"
                state = await _run_timed_step(resume_id, current_step, lambda: generate_cover_letter(state, db))

            current_step = "ats_score"
            state = await _run_timed_step(resume_id, current_step, lambda: score_ats(state, db))

        resume.content_json = state.get("content") or resume.content_json
        resume.latex_source = render_resume_latex(resume.content_json)
        resume.company_name = state.get("company_research", {}).get("company_name") or resume.company_name
        resume.insights_json = {
            **insights,
            "source_content": source_content,
            "jd_analysis": state.get("jd_analysis"),
            "company_research": state.get("company_research"),
            "tailoring_insights": state.get("tailoring_insights", []),
            "_cached_jd": _cache_key_jd(resume.job_description or ""),
            "_cached_company_url": resume.company_url or "",
            "last_step": "completed",
        }
        resume.insights_json.pop("pipeline_error", None)
        resume.status = "completed"

        if resume.inbox_job_id:
            inbox_job = await db.get(InboxJob, resume.inbox_job_id)
            if inbox_job:
                inbox_job.resume_id = resume.id
                inbox_job.status = "resume_ready"

        if state.get("cover_letter_content"):
            await _persist_cover_letter(db, resume, state["cover_letter_content"])

        if state.get("ats_result"):
            await _persist_ats(db, resume, resume.user_id)

        await db.commit()
        await _emit(resume_id, "agent_complete", {"resume_id": resume_id, "status": "completed"})
        log_pipeline_event(logger, resume_id=resume_id, event="complete", status="completed", mode=mode)
        webhook_url = get_stored_webhook_url(resume.insights_json)
        if webhook_url:
            await dispatch_pipeline_webhook(webhook_url, resume, status="completed")
    except Exception as e:
        logger.exception("Pipeline failed for resume %s at step %s", resume.id, current_step)
        await _fail_step(db, resume.id, current_step, str(e))
        failed_insights = dict(resume.insights_json or {})
        failed_insights["pipeline_error"] = str(e)
        failed_insights["last_step"] = current_step
        resume.insights_json = failed_insights
        resume.status = "failed"
        await db.commit()
        await _emit(resume_id, "agent_error", {"error": str(e), "step": current_step})
        log_pipeline_event(
            logger,
            resume_id=resume_id,
            event="complete",
            status="failed",
            mode=mode,
            error=str(e),
            last_step=current_step,
        )
        webhook_url = get_stored_webhook_url(failed_insights)
        if webhook_url:
            await dispatch_pipeline_webhook(
                webhook_url,
                resume,
                status="failed",
                error=str(e),
                last_step=current_step,
            )


async def run_cover_letter_regeneration(db: AsyncSession, letter: CoverLetterDocument, resume: ResumeDocument) -> None:
    """Regenerate cover letter content for an existing cover letter document."""
    letter.status = "processing"
    await db.commit()

    insights = dict(resume.insights_json or {})
    state: PipelineState = PipelineState(
        resume_id=str(resume.id),
        user_id=str(resume.user_id),
        job_description=resume.job_description or "",
        company_url=resume.company_url,
        create_cover_letter=True,
        cover_letter_meta={
            "hiring_manager_name": letter.hiring_manager_name,
            "hiring_manager_email": letter.hiring_manager_email,
            "street_address": letter.street_address,
            "city": letter.city,
            "state_province": letter.state_province,
            "postal_code": letter.postal_code,
            "letter_date": letter.letter_date,
            "additional_context": letter.additional_context,
        },
        content=resume.content_json or {},
        jd_analysis=insights.get("jd_analysis", {}),
        company_research=insights.get("company_research", {}),
    )

    try:
        state = await generate_cover_letter(state, db)
        from app.services.resume.renderer import render_cover_letter_latex

        letter.content_json = state["cover_letter_content"]
        contact = (resume.content_json or {}).get("contact", {})
        letter.latex_source = render_cover_letter_latex(letter.content_json, contact)
        letter.status = "completed"
        await db.commit()
        await _emit(str(resume.id), "agent_complete", {"resume_id": str(resume.id), "cover_letter_id": str(letter.id)})
    except Exception as e:
        logger.exception("Cover letter regeneration failed for %s", letter.id)
        letter.status = "failed"
        await _fail_step(db, resume.id, "cover_letter", str(e))
        await db.commit()
        await _emit(str(resume.id), "agent_error", {"error": str(e), "step": "cover_letter"})
