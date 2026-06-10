from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agents.editor_agent import apply_change, run_editor_agent
from app.agents.graph import run_generation_pipeline
from app.api.schemas import (
    ATSScoreResponse,
    ChangeActionRequest,
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
from app.services.resume.pdf_compiler import compile_latex_to_pdf
from app.services.resume.renderer import render_resume_html, render_resume_latex

router = APIRouter()


async def _get_structured_profile(db: AsyncSession, user: User) -> dict:
    result = await db.execute(select(UserProfileStructured).where(UserProfileStructured.user_id == user.id))
    row = result.scalar_one_or_none()
    if row:
        return row.content_json
    return empty_resume_content().model_dump()


def _resume_response(resume: ResumeDocument, cover_letter_id: UUID | None = None) -> ResumeResponse:
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
        created_at=resume.created_at,
        updated_at=resume.updated_at,
        cover_letter_id=cover_letter_id,
    )


@router.get("", response_model=ResumeListResponse)
async def list_resumes(
    search: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
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
        resumes=[_resume_response(r, cl_map.get(r.id)) for r in resumes],
        total=len(resumes),
    )


@router.post("", response_model=ResumeResponse)
async def create_resume(
    body: ResumeCreate,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
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
    )
    db.add(resume)
    await db.commit()
    await db.refresh(resume)

    async def _run():
        from app.core.database import async_session

        async with async_session() as session:
            result = await session.execute(select(ResumeDocument).where(ResumeDocument.id == resume.id))
            doc = result.scalar_one()
            await run_generation_pipeline(session, doc)

    background_tasks.add_task(_run)
    return _resume_response(resume)


@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(
    resume_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    resume = await _get_resume(db, resume_id, user.id)
    cl_result = await db.execute(select(CoverLetterDocument).where(CoverLetterDocument.resume_id == resume.id))
    cl = cl_result.scalar_one_or_none()
    return _resume_response(resume, cl.id if cl else None)


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
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    resume = await _get_resume(db, resume_id, user.id)
    if body.title is not None:
        resume.title = body.title
    if body.content_json is not None:
        resume.content_json = body.content_json
        resume.latex_source = render_resume_latex(body.content_json)
    if body.latex_source is not None:
        resume.latex_source = body.latex_source
    if body.application_id is not None:
        resume.application_id = body.application_id
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
    format: str = "html",
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    resume = await _get_resume(db, resume_id, user.id)
    if format == "latex":
        return {"latex": resume.latex_source or render_resume_latex(resume.content_json)}
    return Response(content=render_resume_html(resume.content_json), media_type="text/html")


@router.get("/{resume_id}/pdf")
async def export_pdf(
    resume_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    resume = await _get_resume(db, resume_id, user.id)
    latex = resume.latex_source or render_resume_latex(resume.content_json)
    try:
        pdf_bytes = compile_latex_to_pdf(latex)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    return Response(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=resume.pdf"})


@router.get("/{resume_id}/messages", response_model=list[ChatMessageResponse])
async def get_messages(
    resume_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_resume(db, resume_id, user.id)
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.resume_id == resume_id)
        .options(selectinload(ChatMessage.pending_changes))
        .order_by(ChatMessage.created_at)
    )
    messages = result.scalars().all()
    return [
        ChatMessageResponse(
            id=m.id,
            role=m.role,
            content=m.content,
            pending_changes=[PendingChangeResponse.model_validate(c) for c in m.pending_changes],
            created_at=m.created_at,
        )
        for m in messages
    ]


@router.post("/{resume_id}/chat", response_model=ChatMessageResponse)
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
    await db.refresh(msg)
    result = await db.execute(
        select(ChatMessage).where(ChatMessage.id == msg.id).options(selectinload(ChatMessage.pending_changes))
    )
    msg = result.scalar_one()
    return ChatMessageResponse(
        id=msg.id,
        role=msg.role,
        content=msg.content,
        pending_changes=[PendingChangeResponse.model_validate(c) for c in msg.pending_changes],
        created_at=msg.created_at,
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

    if body.action == "accept":
        resume.content_json = apply_change(resume.content_json, change.path, change.new_value or "")
        resume.latex_source = render_resume_latex(resume.content_json)
        change.status = "accepted"
    else:
        change.status = "rejected"

    await db.commit()
    return {"ok": True, "content_json": resume.content_json}


@router.post("/{resume_id}/ats-score", response_model=ATSScoreResponse)
async def run_ats_score(
    resume_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    resume = await _get_resume(db, resume_id, user.id)
    from app.agents.graph import score_ats

    state = {
        "resume_id": str(resume.id),
        "user_id": str(user.id),
        "job_description": resume.job_description or "",
        "content": resume.content_json,
        "jd_analysis": (resume.insights_json or {}).get("jd_analysis", {}),
    }
    state = await score_ats(state, db)

    ats = state["ats_result"]
    row = ATSScore(
        resume_id=resume.id,
        job_description=resume.job_description,
        overall_score=ats["overall_score"],
        keyword_match=ats["keyword_match"],
        formatting_score=ats["formatting_score"],
        suggestions_json={"suggestions": ats.get("suggestions", [])},
        missing_keywords=ats.get("missing_keywords", []),
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return ATSScoreResponse(
        id=row.id,
        overall_score=row.overall_score,
        keyword_match=row.keyword_match,
        formatting_score=row.formatting_score,
        missing_keywords=row.missing_keywords,
        suggestions=ats.get("suggestions", []),
        created_at=row.created_at,
    )


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
    suggestions = (row.suggestions_json or {}).get("suggestions", [])
    return ATSScoreResponse(
        id=row.id,
        overall_score=row.overall_score,
        keyword_match=row.keyword_match,
        formatting_score=row.formatting_score,
        missing_keywords=row.missing_keywords,
        suggestions=suggestions,
        created_at=row.created_at,
    )
