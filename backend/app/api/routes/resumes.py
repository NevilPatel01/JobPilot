from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agents.editor_agent import apply_change, format_path_label, run_editor_agent
from app.agents.graph import run_generation_pipeline
from app.agents.pipeline_status import get_pipeline_status, mark_stale_processing_resumes
from app.services.llm.client import get_user_llm_config
from app.api.schemas import (
    ATSScoreHistoryResponse,
    ATSScoreResponse,
    ATSSuggestionItem,
    BatchChangeActionRequest,
    ChangeActionRequest,
    ChatExchangeResponse,
    ChatMessageResponse,
    ChatRequest,
    CoverLetterListResponse,
    CoverLetterResponse,
    CoverLetterUpdate,
    PendingChangeResponse,
    ResumeCreate,
    ResumeListResponse,
    ResumeResponse,
    ResumeUpdate,
)
from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.cover_letter import CoverLetterDocument
from app.models.profile_structured import UserProfileStructured
from app.models.resume import ATSScore, ChatMessage, PendingChange, ResumeDocument
from app.models.user import User
from app.schemas.resume_content import empty_resume_content
from app.services.ats.persist import save_ats_score
from app.services.resume.pdf_compiler import compile_latex_to_pdf
from app.services.resume.renderer import render_resume_html, render_resume_latex, resolve_export_latex

router = APIRouter()


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


def _pipeline_task(resume_id: UUID, mode: str = "full"):
    async def _run():
        from app.core.database import async_session

        async with async_session() as session:
            result = await session.execute(select(ResumeDocument).where(ResumeDocument.id == resume_id))
            doc = result.scalar_one()
            await run_generation_pipeline(session, doc, mode=mode)  # type: ignore[arg-type]

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


@router.get("", response_model=ResumeListResponse)
async def list_resumes(
    search: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await mark_stale_processing_resumes(db)
    q = select(ResumeDocument).where(ResumeDocument.user_id == user.id).order_by(ResumeDocument.updated_at.desc())
    if search:
        q = q.where(ResumeDocument.title.ilike(f"%{search}%"))
    result = await db.execute(q)
    resumes = result.scalars().all()

    cl_map: dict = {}
    if resumes:
        cl_result = await db.execute(
            select(CoverLetterDocument).where(
                CoverLetterDocument.user_id == user.id,
                CoverLetterDocument.resume_id.in_([r.id for r in resumes]),
            )
        )
        for cl in cl_result.scalars().all():
            if cl.resume_id:
                cl_map[cl.resume_id] = cl.id

    return ResumeListResponse(
        resumes=[
            _resume_response(
                r,
                cl_map.get(r.id),
                pipeline_error=(r.insights_json or {}).get("pipeline_error") if r.status == "failed" else None,
                last_step=(r.insights_json or {}).get("last_step"),
            )
            for r in resumes
        ],
        total=len(resumes),
    )


@router.post("", response_model=ResumeResponse)
async def create_resume(
    body: ResumeCreate,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _require_llm_config(db, user.id)

    if body.source_type == "profile":
        content = await _get_structured_profile(db, user)
    else:
        content = body.content_json or empty_resume_content().model_dump()

    resume = ResumeDocument(
        user_id=user.id,
        title=body.title,
        status="processing",
        job_description=body.job_description,
        company_url=body.company_url,
        source_type=body.source_type,
        content_json=content,
        latex_source=render_resume_latex(content),
        create_cover_letter=body.create_cover_letter,
        cover_letter_meta=body.cover_letter_meta.model_dump() if body.cover_letter_meta else None,
        insights_json={"source_content": content},
    )
    db.add(resume)
    await db.commit()
    await db.refresh(resume)

    background_tasks.add_task(_pipeline_task(resume.id, "full"))
    return _resume_response(resume)


@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(
    resume_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await mark_stale_processing_resumes(db)
    resume = await _get_resume(db, resume_id, user.id)
    cl_result = await db.execute(select(CoverLetterDocument).where(CoverLetterDocument.resume_id == resume.id))
    cl = cl_result.scalar_one_or_none()
    return await _resume_response_with_status(db, resume, cl.id if cl else None)


async def _get_resume(db: AsyncSession, resume_id: UUID, user_id: UUID) -> ResumeDocument:
    result = await db.execute(
        select(ResumeDocument).where(ResumeDocument.id == resume_id, ResumeDocument.user_id == user_id)
    )
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return resume


@router.patch("/{resume_id}", response_model=ResumeResponse)
async def update_resume(
    resume_id: UUID,
    body: ResumeUpdate,
    rescore: bool = Query(False),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    resume = await _get_resume(db, resume_id, user.id)
    if body.title is not None:
        resume.title = body.title
    if body.content_json is not None:
        resume.content_json = body.content_json
    if body.latex_source is not None:
        resume.latex_source = body.latex_source
    if body.application_id is not None:
        resume.application_id = body.application_id
    await db.commit()
    if rescore and body.content_json is not None:
        await save_ats_score(db, resume, user.id, enrich_llm=True)
        await db.commit()
    await db.refresh(resume)
    return _resume_response(resume)


@router.delete("/{resume_id}")
async def delete_resume(
    resume_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    resume = await _get_resume(db, resume_id, user.id)
    await db.delete(resume)
    await db.commit()
    return {"ok": True}


@router.get("/{resume_id}/preview")
async def preview_resume(
    resume_id: UUID,
    format: str = "latex",
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    resume = await _get_resume(db, resume_id, user.id)
    if format == "html":
        return Response(content=render_resume_html(resume.content_json), media_type="text/html")
    return {"latex": resolve_export_latex(resume.content_json, resume.latex_source)}


@router.get("/{resume_id}/pdf")
async def export_pdf(
    resume_id: UUID,
    inline: bool = Query(False, description="Use inline disposition for browser PDF preview"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    resume = await _get_resume(db, resume_id, user.id)
    latex = resolve_export_latex(resume.content_json, resume.latex_source)
    try:
        pdf_bytes = compile_latex_to_pdf(latex)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    disposition = "inline" if inline else "attachment"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'{disposition}; filename="resume.pdf"'},
    )


@router.post("/{resume_id}/regenerate-latex", response_model=ResumeResponse)
async def regenerate_latex(
    resume_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    resume = await _get_resume(db, resume_id, user.id)
    resume.latex_source = render_resume_latex(resume.content_json)
    await db.commit()
    await db.refresh(resume)
    return _resume_response(resume)


@router.get("/{resume_id}/messages", response_model=list[ChatMessageResponse])
async def get_messages(
    resume_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    resume = await _get_resume(db, resume_id, user.id)
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.resume_id == resume_id)
        .options(selectinload(ChatMessage.pending_changes))
        .order_by(ChatMessage.created_at)
    )
    messages = result.scalars().all()
    return [_chat_message_response(m, resume.content_json) for m in messages]


@router.post("/{resume_id}/chat", response_model=ChatExchangeResponse)
async def chat_edit(
    resume_id: UUID,
    body: ChatRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    resume = await _get_resume(db, resume_id, user.id)

    pending = await db.execute(
        select(PendingChange)
        .join(ChatMessage)
        .where(ChatMessage.resume_id == resume_id, PendingChange.status == "pending")
    )
    if pending.scalars().first():
        raise HTTPException(status_code=409, detail="Approve or reject pending changes first")

    user_msg = ChatMessage(resume_id=resume.id, role="user", content=body.message)
    db.add(user_msg)
    await db.flush()

    reply, changes = await run_editor_agent(db, user.id, resume.content_json, body.message, resume.job_description or "")

    msg = ChatMessage(resume_id=resume.id, role="assistant", content=reply)
    db.add(msg)
    await db.flush()

    for ch in changes:
        db.add(
            PendingChange(
                message_id=msg.id,
                path=ch["path"],
                old_value=ch.get("old_value"),
                new_value=ch.get("new_value"),
                status="pending",
            )
        )
    await db.commit()

    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.id.in_([user_msg.id, msg.id]))
        .options(selectinload(ChatMessage.pending_changes))
        .order_by(ChatMessage.created_at)
    )
    loaded = {m.id: m for m in result.scalars().all()}
    user_loaded = loaded[user_msg.id]
    assistant_loaded = loaded[msg.id]
    content = resume.content_json
    return ChatExchangeResponse(
        user_message=_chat_message_response(user_loaded, content),
        assistant_message=_chat_message_response(assistant_loaded, content),
    )


@router.post("/{resume_id}/changes")
async def handle_change(
    resume_id: UUID,
    body: ChangeActionRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    resume = await _get_resume(db, resume_id, user.id)
    result = await db.execute(
        select(PendingChange)
        .join(ChatMessage)
        .where(PendingChange.id == body.change_id, ChatMessage.resume_id == resume_id)
    )
    change = result.scalar_one_or_none()
    if not change:
        raise HTTPException(status_code=404, detail="Change not found")

    ats_score = await _apply_pending_changes(db, resume, user.id, [change], body.action)
    return {"ok": True, "content_json": resume.content_json, "ats_score": ats_score}


async def _apply_pending_changes(
    db: AsyncSession,
    resume: ResumeDocument,
    user_id: UUID,
    changes: list[PendingChange],
    action: str,
) -> ATSScoreResponse | None:
    if action == "accept":
        for change in changes:
            resume.content_json = apply_change(resume.content_json, change.path, change.new_value or "")
            change.status = "accepted"
        resume.latex_source = render_resume_latex(resume.content_json)
    else:
        for change in changes:
            change.status = "rejected"

    await db.commit()

    if action != "accept":
        return None
    ats_row = await save_ats_score(db, resume, user_id, enrich_llm=True)
    await db.commit()
    return _ats_response(ats_row)


@router.post("/{resume_id}/changes/batch")
async def handle_changes_batch(
    resume_id: UUID,
    body: BatchChangeActionRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not body.change_ids:
        raise HTTPException(status_code=400, detail="No change IDs provided")

    resume = await _get_resume(db, resume_id, user.id)
    result = await db.execute(
        select(PendingChange)
        .join(ChatMessage)
        .where(
            PendingChange.id.in_(body.change_ids),
            ChatMessage.resume_id == resume_id,
            PendingChange.status == "pending",
        )
    )
    changes = result.scalars().all()
    if len(changes) != len(body.change_ids):
        raise HTTPException(status_code=404, detail="One or more pending changes were not found")

    ats_score = await _apply_pending_changes(db, resume, user.id, changes, body.action)
    return {"ok": True, "content_json": resume.content_json, "ats_score": ats_score}


@router.post("/{resume_id}/ats-score", response_model=ATSScoreResponse)
async def run_ats_score(
    resume_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    resume = await _get_resume(db, resume_id, user.id)
    row = await save_ats_score(db, resume, user.id, enrich_llm=True)
    await db.commit()
    await db.refresh(row)
    return _ats_response(row)


@router.get("/{resume_id}/ats-score/history", response_model=ATSScoreHistoryResponse)
async def get_ats_history(
    resume_id: UUID,
    limit: int = Query(5, ge=1, le=20),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_resume(db, resume_id, user.id)
    result = await db.execute(
        select(ATSScore)
        .where(ATSScore.resume_id == resume_id)
        .order_by(ATSScore.created_at.desc())
        .limit(limit)
    )
    rows = result.scalars().all()
    return ATSScoreHistoryResponse(scores=[_ats_response(r) for r in rows], total=len(rows))


@router.get("/{resume_id}/ats-score", response_model=ATSScoreResponse | None)
async def get_latest_ats(
    resume_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_resume(db, resume_id, user.id)
    result = await db.execute(
        select(ATSScore).where(ATSScore.resume_id == resume_id).order_by(ATSScore.created_at.desc()).limit(1)
    )
    row = result.scalar_one_or_none()
    if not row:
        return None
    return _ats_response(row)


@router.post("/{resume_id}/regenerate", response_model=ResumeResponse)
async def regenerate_resume(
    resume_id: UUID,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _require_llm_config(db, user.id)
    resume = await _get_resume(db, resume_id, user.id)
    await _ensure_not_processing(resume)
    background_tasks.add_task(_pipeline_task(resume.id, "full"))
    resume.status = "processing"
    await db.commit()
    await db.refresh(resume)
    return _resume_response(resume)


@router.post("/{resume_id}/regenerate/resume", response_model=ResumeResponse)
async def regenerate_tailored_resume(
    resume_id: UUID,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _require_llm_config(db, user.id)
    resume = await _get_resume(db, resume_id, user.id)
    await _ensure_not_processing(resume)
    background_tasks.add_task(_pipeline_task(resume.id, "tailor_only"))
    resume.status = "processing"
    await db.commit()
    await db.refresh(resume)
    return _resume_response(resume)
