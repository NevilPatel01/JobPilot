from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.editor_agent import format_path_label
from app.agents.pipeline_status import get_pipeline_status
from app.api.schemas import (
    ATSScoreResponse,
    ATSSuggestionItem,
    ChatMessageResponse,
    PendingChangeResponse,
    ResumeResponse,
)
from app.models.profile_structured import UserProfileStructured
from app.models.resume import ATSScore, ChatMessage, PendingChange, ResumeDocument
from app.models.user import User
from app.schemas.resume_content import empty_resume_content
from app.services.llm.client import get_user_llm_config


def _pending_change_response(change: PendingChange, content: dict) -> PendingChangeResponse:
    return PendingChangeResponse(
        id=change.id,
        path=change.path,
        path_label=format_path_label(content, change.path),
        old_value=change.old_value,
        new_value=change.new_value,
        status=change.status,
    )


def _chat_message_response(message: ChatMessage, content: dict) -> ChatMessageResponse:
    return ChatMessageResponse(
        id=message.id,
        role=message.role,
        content=message.content,
        pending_changes=[_pending_change_response(c, content) for c in message.pending_changes],
        created_at=message.created_at,
    )


def _ats_response(row: ATSScore, suggestions: list[str] | None = None) -> ATSScoreResponse:
    payload = row.suggestions_json or {}
    items_raw = payload.get("items") or []
    items = [ATSSuggestionItem.model_validate(i) for i in items_raw if isinstance(i, dict)]
    return ATSScoreResponse(
        id=row.id,
        overall_score=row.overall_score,
        keyword_match=row.keyword_match,
        formatting_score=row.formatting_score,
        semantic_score=row.semantic_score or 0,
        skills_coverage=row.skills_coverage or 0,
        section_score=row.section_score or 0,
        matched_keywords=row.matched_keywords,
        missing_keywords=row.missing_keywords,
        suggestions=suggestions if suggestions is not None else payload.get("suggestions", []),
        suggestion_items=items,
        breakdown=row.breakdown_json,
        created_at=row.created_at,
    )


async def _get_structured_profile(db: AsyncSession, user: User) -> dict:
    result = await db.execute(select(UserProfileStructured).where(UserProfileStructured.user_id == user.id))
    row = result.scalar_one_or_none()
    if row:
        return row.content_json
    return empty_resume_content().model_dump()


def _resume_response(
    resume: ResumeDocument,
    cover_letter_id: UUID | None = None,
    pipeline_error: str | None = None,
    last_step: str | None = None,
) -> ResumeResponse:
    insights = resume.insights_json or {}
    return ResumeResponse(
        id=resume.id,
        title=resume.title,
        job_title=insights.get("job_title"),
        job_url=insights.get("job_url"),
        status=resume.status,
        job_description=resume.job_description,
        company_url=resume.company_url,
        company_name=resume.company_name,
        source_type=resume.source_type,
        content_json=resume.content_json,
        latex_source=resume.latex_source,
        insights_json=resume.insights_json,
        create_cover_letter=resume.create_cover_letter,
        cover_letter_meta=resume.cover_letter_meta,
        application_id=resume.application_id,
        job_id=resume.job_id,
        inbox_job_id=resume.inbox_job_id,
        resume_category=resume.resume_category,
        why_this_version=resume.why_this_version,
        created_at=resume.created_at,
        updated_at=resume.updated_at,
        cover_letter_id=cover_letter_id,
        pipeline_error=pipeline_error or insights.get("pipeline_error"),
        last_step=last_step or insights.get("last_step"),
    )


async def _resume_response_with_status(
    db: AsyncSession,
    resume: ResumeDocument,
    cover_letter_id: UUID | None = None,
) -> ResumeResponse:
    last_step, pipeline_error = await get_pipeline_status(db, resume.id)
    if resume.status != "failed":
        pipeline_error = None
    insights = resume.insights_json or {}
    return _resume_response(
        resume,
        cover_letter_id,
        pipeline_error=pipeline_error or insights.get("pipeline_error"),
        last_step=last_step or insights.get("last_step"),
    )


def _pipeline_task(resume_id: UUID, mode: str = "full", aggressive: bool = False):
    async def _run():
        from app.core.database import async_session
        from app.agents.graph import run_generation_pipeline

        async with async_session() as session:
            result = await session.execute(select(ResumeDocument).where(ResumeDocument.id == resume_id))
            doc = result.scalar_one()
            await run_generation_pipeline(session, doc, mode=mode, aggressive=aggressive)  # type: ignore[arg-type]

    return _run


async def _ensure_not_processing(resume: ResumeDocument) -> None:
    if resume.status == "processing":
        raise HTTPException(status_code=409, detail="Resume is still processing. Wait for completion or retry later.")


async def _require_llm_config(db: AsyncSession, user_id: UUID) -> None:
    if not await get_user_llm_config(db, user_id):
        raise HTTPException(
            status_code=422,
            detail="Configure an LLM API key in Settings before generating or regenerating resumes.",
        )


async def _get_resume(db: AsyncSession, resume_id: UUID, user_id: UUID) -> ResumeDocument:
    result = await db.execute(
        select(ResumeDocument).where(ResumeDocument.id == resume_id, ResumeDocument.user_id == user_id)
    )
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return resume
