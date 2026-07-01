"""Pipeline orchestration — runs all steps and persists results."""

import logging
from typing import Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.pipeline_helpers import PipelineState, emit, fail_step, run_timed_step
from app.agents.steps.analyze import analyze_jd
from app.agents.steps.ats import score_ats
from app.agents.steps.cover_letter import generate_cover_letter
from app.agents.steps.ingest import ingest_context
from app.agents.steps.research import research_company_step
from app.agents.steps.tailor import refine_for_ats, tailor_resume
from app.core.pipeline_logging import log_pipeline_event
from app.models.cover_letter import CoverLetterDocument
from app.models.job_intelligence import InboxJob
from app.models.resume import ResumeDocument
from app.services.ats.persist import save_ats_score
from app.services.resume.renderer import render_resume_latex
from app.services.webhook import dispatch_pipeline_webhook, get_stored_webhook_url

logger = logging.getLogger(__name__)
PipelineMode = Literal["full", "tailor_only", "cover_letter_only"]

ATS_TARGET = 85
MAX_ATS_REFINES = 3


async def _iterate_to_target_ats(state: PipelineState, db: AsyncSession, resume_id: str) -> PipelineState:
    """Score-guided refinement loop: while below target, weave in the missing
    keywords the scorer flagged and re-score. Stop at the target, when it stops
    improving, or after MAX_ATS_REFINES attempts."""
    from app.services.ats.scorer import score_resume

    result = state.get("ats_result") or {}
    for attempt in range(1, MAX_ATS_REFINES + 1):
        score = result.get("overall_score", 0)
        if score >= ATS_TARGET:
            break
        try:
            improved = await refine_for_ats(state, db, result)
        except Exception as e:  # no key / LLM error — keep the best result so far
            logger.warning("ATS refine attempt %s failed: %s", attempt, e)
            break
        new_result = score_resume(
            improved, state.get("job_description", ""), state.get("jd_analysis") or {}
        ).to_dict()
        if new_result.get("overall_score", 0) <= score:
            break  # no improvement — don't churn the content further
        state["content"] = improved
        state["ats_result"] = new_result
        result = new_result
        await emit(resume_id, "agent_step", {"step": "ats_score", "status": "completed", "data": new_result})
    return state


def _cache_key_jd(jd: str) -> str:
    return jd[:500]


def _should_reuse_analysis(insights: dict, job_description: str, company_url: str | None) -> bool:
    if insights.get("_cached_jd") != _cache_key_jd(job_description or ""):
        return False
    if (insights.get("_cached_company_url") or "") != (company_url or ""):
        return False
    return bool(insights.get("jd_analysis"))


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


async def run_generation_pipeline(
    db: AsyncSession,
    resume: ResumeDocument,
    mode: PipelineMode = "full",
    aggressive: bool = False,
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
        aggressive=aggressive,
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
            state = await run_timed_step(resume_id, current_step, lambda: generate_cover_letter(state, db))
        elif mode == "tailor_only":
            state["jd_analysis"] = insights.get("jd_analysis", {})
            state["company_research"] = insights.get("company_research", {})
            current_step = "tailor_resume"
            state = await run_timed_step(resume_id, current_step, lambda: tailor_resume(state, db))
            current_step = "ats_score"
            state = await run_timed_step(resume_id, current_step, lambda: score_ats(state, db))
        else:
            current_step = "ingest_context"
            state = await run_timed_step(resume_id, current_step, lambda: ingest_context(state, db))

            if reuse_analysis and state.get("jd_analysis"):
                await emit(resume_id, "agent_step", {"step": "analyze_jd", "status": "completed", "cached": True})
                log_pipeline_event(logger, resume_id=resume_id, event="step", status="cached", mode=mode)
            else:
                current_step = "analyze_jd"
                state = await run_timed_step(resume_id, current_step, lambda: analyze_jd(state, db))

            current_step = "research_company"
            state = await run_timed_step(
                resume_id,
                current_step,
                lambda: research_company_step(state, db, reuse=reuse_analysis and bool(state.get("company_research"))),
            )

            current_step = "tailor_resume"
            state = await run_timed_step(resume_id, current_step, lambda: tailor_resume(state, db))

            if state.get("create_cover_letter"):
                current_step = "cover_letter"
                state = await run_timed_step(resume_id, current_step, lambda: generate_cover_letter(state, db))

            current_step = "ats_score"
            state = await run_timed_step(resume_id, current_step, lambda: score_ats(state, db))

        # Iterate toward the ATS target by weaving in missing keywords, then re-scoring.
        if mode in ("full", "tailor_only") and state.get("ats_result"):
            current_step = "ats_refine"
            state = await _iterate_to_target_ats(state, db, resume_id)

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
            await save_ats_score(db, resume, resume.user_id, enrich_llm=True)

        await db.commit()
        await emit(resume_id, "agent_complete", {"resume_id": resume_id, "status": "completed"})
        log_pipeline_event(logger, resume_id=resume_id, event="complete", status="completed", mode=mode)
        webhook_url = get_stored_webhook_url(resume.insights_json)
        if webhook_url:
            await dispatch_pipeline_webhook(webhook_url, resume, status="completed")
    except Exception as e:
        logger.exception("Pipeline failed for resume %s at step %s", resume.id, current_step)
        await fail_step(db, resume.id, current_step, str(e))
        failed_insights = dict(resume.insights_json or {})
        failed_insights["pipeline_error"] = str(e)
        failed_insights["last_step"] = current_step
        resume.insights_json = failed_insights
        resume.status = "failed"
        await db.commit()
        await emit(resume_id, "agent_error", {"error": str(e), "step": current_step})
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
            await dispatch_pipeline_webhook(webhook_url, resume, status="failed", error=str(e), last_step=current_step)


async def run_cover_letter_regeneration(db: AsyncSession, letter: CoverLetterDocument, resume: ResumeDocument) -> None:
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
        await emit(str(resume.id), "agent_complete", {"resume_id": str(resume.id), "cover_letter_id": str(letter.id)})
    except Exception as e:
        logger.exception("Cover letter regeneration failed for %s", letter.id)
        letter.status = "failed"
        await fail_step(db, resume.id, "cover_letter", str(e))
        await db.commit()
        await emit(str(resume.id), "agent_error", {"error": str(e), "step": "cover_letter"})
