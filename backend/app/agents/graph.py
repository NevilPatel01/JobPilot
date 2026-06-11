import json
import logging
from typing import Any, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cover_letter import CoverLetterDocument
from app.models.resume import AgentRun, ATSScore, ResumeDocument
from app.schemas.resume_content import CoverLetterContent, ResumeContent, resume_to_text
from app.scrapers.company_researcher import research_company
from app.services.llm.client import create_chat_model, get_user_llm_config
from app.services.rag.ingest import ingest_text, search_chunks
from app.services.resume.renderer import render_resume_latex
from app.sockets.chat import sio

logger = logging.getLogger(__name__)


class PipelineState(TypedDict, total=False):
    resume_id: str
    user_id: str
    job_description: str
    company_url: str | None
    create_cover_letter: bool
    cover_letter_meta: dict
    content: dict
    company_research: dict
    jd_analysis: dict
    tailoring_insights: list[str]
    cover_letter_content: dict
    ats_result: dict
    error: str | None


async def _emit(resume_id: str, event: str, data: dict) -> None:
    await sio.emit(event, data, room=f"resume:{resume_id}")


async def _run_step(db: AsyncSession, resume_id, agent_type: str, status: str, steps: dict | None = None, error: str | None = None):
    run = AgentRun(resume_id=resume_id, agent_type=agent_type, status=status, steps_json=steps, error=error)
    db.add(run)
    await db.flush()


async def ingest_context(state: PipelineState, db: AsyncSession) -> PipelineState:
    resume_id = state["resume_id"]
    await _emit(resume_id, "agent_step", {"step": "ingest_context", "status": "running"})
    llm_config = await get_user_llm_config(db, state["user_id"])
    if llm_config and state.get("job_description"):
        await ingest_text(db, state["user_id"], "job_description", resume_id, state["job_description"], llm_config)
    await _run_step(db, resume_id, "ingest_context", "completed")
    await _emit(resume_id, "agent_step", {"step": "ingest_context", "status": "completed"})
    return state


async def analyze_jd(state: PipelineState, db: AsyncSession) -> PipelineState:
    resume_id = state["resume_id"]
    await _emit(resume_id, "agent_step", {"step": "analyze_jd", "status": "running"})
    llm_config = await get_user_llm_config(db, state["user_id"])
    jd = state.get("job_description", "")

    if not llm_config or not jd:
        state["jd_analysis"] = {"sections": [], "keywords": []}
        return state

    llm = create_chat_model(llm_config)
    prompt = f"""Analyze this job description and return JSON with keys:
- required_skills: list of strings
- responsibilities: list of strings
- seniority: string
- keywords: list of important ATS keywords

Job Description:
{jd[:6000]}"""
    try:
        res = await llm.ainvoke([SystemMessage(content="Return valid JSON only."), HumanMessage(content=prompt)])
        parsed = json.loads(res.content if isinstance(res.content, str) else str(res.content))
        state["jd_analysis"] = parsed
    except Exception as e:
        logger.warning("JD analysis failed: %s", e)
        state["jd_analysis"] = {"keywords": [], "required_skills": [], "responsibilities": []}

    await _run_step(db, resume_id, "analyze_jd", "completed", state["jd_analysis"])
    await _emit(resume_id, "agent_step", {"step": "analyze_jd", "status": "completed", "data": state["jd_analysis"]})
    return state


async def research_company_step(state: PipelineState, db: AsyncSession) -> PipelineState:
    resume_id = state["resume_id"]
    url = state.get("company_url")
    if not url:
        state["company_research"] = {}
        return state

    await _emit(resume_id, "agent_step", {"step": "research_company", "status": "running"})
    try:
        research = await research_company(url)
        state["company_research"] = research
        llm_config = await get_user_llm_config(db, state["user_id"])
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
    content = ResumeContent.model_validate(state.get("content") or {})

    if not llm_config:
        state["content"] = content.model_dump()
        state["tailoring_insights"] = ["No API key configured — using profile as-is."]
        await _emit(resume_id, "agent_step", {"step": "tailor_resume", "status": "completed"})
        return state

    llm = create_chat_model(llm_config)
    chunks = await search_chunks(db, state["user_id"], state.get("job_description", ""), llm_config)
    rag_context = "\n---\n".join(c.chunk_text for c in chunks[:6])
    jd = json.dumps(state.get("jd_analysis", {}))
    company = state.get("company_research", {}).get("summary", "")

    prompt = f"""Tailor this resume JSON for the target job. Return ONLY valid JSON matching the same schema.
Improve bullet points with metrics and keywords from the JD. Do not invent employers or degrees.

Current resume:
{content.model_dump_json()}

JD analysis: {jd}
Company context: {company}
RAG context: {rag_context[:4000]}"""

    try:
        res = await llm.ainvoke([
            SystemMessage(content="You are an expert resume writer. Return only JSON."),
            HumanMessage(content=prompt),
        ])
        raw = res.content if isinstance(res.content, str) else str(res.content)
        tailored = json.loads(raw)
        state["content"] = ResumeContent.model_validate(tailored).model_dump()
        state["tailoring_insights"] = [
            "Aligned experience bullets with job requirements",
            "Incorporated company context into summary and bullets",
            "Optimized keywords for ATS parsing",
        ]
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
    content = CoverLetterContent(
        recipient_name=meta.get("hiring_manager_name", ""),
        company_name=state.get("company_research", {}).get("company_name", ""),
        company_address=", ".join(filter(None, [meta.get("street_address"), meta.get("city"), meta.get("state_province"), meta.get("postal_code")])),
        date=meta.get("letter_date", ""),
        salutation=f"Dear {meta.get('hiring_manager_name') or 'Hiring Manager'},",
    )

    if llm_config:
        llm = create_chat_model(llm_config, temperature=0.5)
        resume_text = resume_to_text(ResumeContent.model_validate(state["content"]))
        prompt = f"""Write a professional cover letter as JSON with keys: paragraphs (list of strings), closing (string).
Use hiring manager: {meta.get('hiring_manager_name', 'Hiring Manager')}
Additional context: {meta.get('additional_context', '')}
Job description excerpt: {state.get('job_description', '')[:2000]}
Resume summary: {resume_text[:3000]}"""
        try:
            res = await llm.ainvoke([SystemMessage(content="Return valid JSON only."), HumanMessage(content=prompt)])
            parsed = json.loads(res.content if isinstance(res.content, str) else str(res.content))
            content.paragraphs = parsed.get("paragraphs", [])
            content.closing = parsed.get("closing", "Sincerely,")
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


def _should_cover_letter(state: PipelineState) -> str:
    return "cover_letter" if state.get("create_cover_letter") else "ats_score"


async def run_generation_pipeline(db: AsyncSession, resume: ResumeDocument) -> None:
    state: PipelineState = {
        "resume_id": str(resume.id),
        "user_id": str(resume.user_id),
        "job_description": resume.job_description or "",
        "company_url": resume.company_url,
        "create_cover_letter": resume.create_cover_letter,
        "cover_letter_meta": resume.cover_letter_meta or {},
        "content": resume.content_json or {},
    }

    try:
        resume.status = "processing"
        await db.commit()

        state = await ingest_context(state, db)
        state = await analyze_jd(state, db)
        state = await research_company_step(state, db)
        state = await tailor_resume(state, db)

        if state.get("create_cover_letter"):
            state = await generate_cover_letter(state, db)

        state = await score_ats(state, db)

        resume.content_json = state.get("content") or resume.content_json
        resume.latex_source = render_resume_latex(resume.content_json)
        resume.company_name = state.get("company_research", {}).get("company_name") or resume.company_name
        resume.insights_json = {
            "jd_analysis": state.get("jd_analysis"),
            "company_research": state.get("company_research"),
            "tailoring_insights": state.get("tailoring_insights", []),
        }
        resume.status = "completed"

        if state.get("cover_letter_content"):
            meta = resume.cover_letter_meta or {}
            cl = CoverLetterDocument(
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
                content_json=state["cover_letter_content"],
            )
            db.add(cl)

        ats = state.get("ats_result")
        if ats:
            db.add(
                ATSScore(
                    resume_id=resume.id,
                    job_description=resume.job_description,
                    overall_score=ats["overall_score"],
                    keyword_match=ats["keyword_match"],
                    formatting_score=ats["formatting_score"],
                    semantic_score=ats.get("semantic_score", 0),
                    skills_coverage=ats.get("skills_coverage", 0),
                    section_score=ats.get("section_score", 0),
                    matched_keywords=ats.get("matched_keywords", []),
                    suggestions_json={"suggestions": ats.get("suggestions", [])},
                    breakdown_json=ats.get("breakdown"),
                    missing_keywords=ats.get("missing_keywords", []),
                )
            )

        await db.commit()
        await _emit(str(resume.id), "agent_complete", {"resume_id": str(resume.id), "status": "completed"})
    except Exception as e:
        logger.exception("Pipeline failed for resume %s", resume.id)
        resume.status = "failed"
        await db.commit()
        await _emit(str(resume.id), "agent_error", {"error": str(e)})
