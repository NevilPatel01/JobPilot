from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agents.cover_letter_agent import apply_change, run_cover_letter_agent
from app.agents.graph import run_cover_letter_regeneration
from app.api.schemas import (
    ChangeActionRequest,
    ChatExchangeResponse,
    ChatMessageResponse,
    ChatRequest,
    CoverLetterCreate,
    CoverLetterListResponse,
    CoverLetterResponse,
    CoverLetterUpdate,
    PendingChangeResponse,
)
from app.api.routes.resumes import _require_llm_config
from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.cover_letter import CoverLetterChatMessage, CoverLetterDocument, CoverLetterPendingChange
from app.models.resume import ResumeDocument
from app.models.user import User
from app.services.resume.pdf_compiler import compile_latex_to_pdf
from app.services.resume.renderer import render_cover_letter_html, render_cover_letter_latex

router = APIRouter()

_HEADER_FIELDS = (
    "hiring_manager_name",
    "hiring_manager_email",
    "street_address",
    "city",
    "state_province",
    "postal_code",
    "letter_date",
    "additional_context",
)


async def _get_letter(db: AsyncSession, letter_id: UUID, user_id: UUID) -> CoverLetterDocument:
    result = await db.execute(
        select(CoverLetterDocument).where(CoverLetterDocument.id == letter_id, CoverLetterDocument.user_id == user_id)
    )
    letter = result.scalar_one_or_none()
    if not letter:
        raise HTTPException(status_code=404, detail="Cover letter not found")
    return letter


async def _get_contact(db: AsyncSession, letter: CoverLetterDocument) -> dict:
    if not letter.resume_id:
        return {}
    res = await db.execute(select(ResumeDocument).where(ResumeDocument.id == letter.resume_id))
    resume = res.scalar_one_or_none()
    if resume:
        return resume.content_json.get("contact", {})
    return {}


def _sync_content_header(letter: CoverLetterDocument) -> None:
    """Keep content_json header fields aligned with document metadata."""
    content = dict(letter.content_json or {})
    if letter.hiring_manager_name:
        content["recipient_name"] = letter.hiring_manager_name
    address = ", ".join(
        filter(
            None,
            [letter.street_address, letter.city, letter.state_province, letter.postal_code],
        )
    )
    if address:
        content["company_address"] = address
    if letter.letter_date:
        content["date"] = letter.letter_date
    if letter.hiring_manager_name:
        content["salutation"] = f"Dear {letter.hiring_manager_name},"
    letter.content_json = content


@router.get("", response_model=CoverLetterListResponse)
async def list_cover_letters(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CoverLetterDocument)
        .where(CoverLetterDocument.user_id == user.id)
        .order_by(CoverLetterDocument.updated_at.desc())
    )
    letters = result.scalars().all()
    return CoverLetterListResponse(cover_letters=[CoverLetterResponse.model_validate(cl) for cl in letters], total=len(letters))


@router.post("", response_model=CoverLetterResponse)
async def create_cover_letter(
    body: CoverLetterCreate,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _require_llm_config(db, user.id)
    if not body.resume_id:
        raise HTTPException(status_code=400, detail="resume_id is required to generate a cover letter.")

    res = await db.execute(
        select(ResumeDocument).where(ResumeDocument.id == body.resume_id, ResumeDocument.user_id == user.id)
    )
    resume = res.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    existing = await db.execute(
        select(CoverLetterDocument).where(CoverLetterDocument.resume_id == resume.id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="This resume already has a cover letter.")

    letter = CoverLetterDocument(
        user_id=user.id,
        resume_id=resume.id,
        title=body.title or f"{resume.title} — Cover Letter",
        status="processing",
        hiring_manager_name=body.hiring_manager_name,
        hiring_manager_email=body.hiring_manager_email,
        street_address=body.street_address,
        city=body.city,
        state_province=body.state_province,
        postal_code=body.postal_code,
        letter_date=body.letter_date,
        additional_context=body.additional_context,
        content_json=body.content_json or {},
    )
    _sync_content_header(letter)
    db.add(letter)
    await db.commit()
    await db.refresh(letter)

    letter_id = letter.id

    async def _run():
        from app.core.database import async_session

        async with async_session() as session:
            l_result = await session.execute(select(CoverLetterDocument).where(CoverLetterDocument.id == letter_id))
            l_doc = l_result.scalar_one()
            r_result = await session.execute(select(ResumeDocument).where(ResumeDocument.id == l_doc.resume_id))
            r_doc = r_result.scalar_one()
            await run_cover_letter_regeneration(session, l_doc, r_doc)

    background_tasks.add_task(_run())
    return CoverLetterResponse.model_validate(letter)


@router.get("/{letter_id}", response_model=CoverLetterResponse)
async def get_cover_letter(
    letter_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    letter = await _get_letter(db, letter_id, user.id)
    return CoverLetterResponse.model_validate(letter)


@router.patch("/{letter_id}", response_model=CoverLetterResponse)
async def update_cover_letter(
    letter_id: UUID,
    body: CoverLetterUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    letter = await _get_letter(db, letter_id, user.id)
    if body.title is not None:
        letter.title = body.title
    if body.content_json is not None:
        letter.content_json = body.content_json
    for field in _HEADER_FIELDS:
        value = getattr(body, field, None)
        if value is not None:
            setattr(letter, field, value)
    _sync_content_header(letter)
    contact = await _get_contact(db, letter)
    # An explicit latex_source override wins (intentional raw-LaTeX save);
    # otherwise keep the LaTeX in sync with the structured content + header.
    if body.latex_source is not None:
        letter.latex_source = body.latex_source
    else:
        letter.latex_source = render_cover_letter_latex(letter.content_json, contact)
    await db.commit()
    await db.refresh(letter)
    return CoverLetterResponse.model_validate(letter)


@router.delete("/{letter_id}")
async def delete_cover_letter(
    letter_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    letter = await _get_letter(db, letter_id, user.id)
    await db.delete(letter)
    await db.commit()
    return {"ok": True}


@router.get("/{letter_id}/preview")
async def preview_cover_letter(
    letter_id: UUID,
    format: str = "html",
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    letter = await _get_letter(db, letter_id, user.id)
    contact = await _get_contact(db, letter)
    if format == "latex":
        latex = letter.latex_source or render_cover_letter_latex(letter.content_json, contact)
        return {"latex": latex}
    return Response(content=render_cover_letter_html(letter.content_json, contact), media_type="text/html")


@router.get("/{letter_id}/pdf")
async def export_cover_letter_pdf(
    letter_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    letter = await _get_letter(db, letter_id, user.id)
    contact = await _get_contact(db, letter)
    latex = letter.latex_source or render_cover_letter_latex(letter.content_json, contact)
    try:
        pdf_bytes = compile_latex_to_pdf(latex)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    filename = f"{letter.title.replace(' ', '_')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{letter_id}/messages", response_model=list[ChatMessageResponse])
async def get_cover_letter_messages(
    letter_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_letter(db, letter_id, user.id)
    result = await db.execute(
        select(CoverLetterChatMessage)
        .where(CoverLetterChatMessage.cover_letter_id == letter_id)
        .options(selectinload(CoverLetterChatMessage.pending_changes))
        .order_by(CoverLetterChatMessage.created_at)
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


def _cover_letter_chat_response(message: CoverLetterChatMessage) -> ChatMessageResponse:
    return ChatMessageResponse(
        id=message.id,
        role=message.role,
        content=message.content,
        pending_changes=[PendingChangeResponse.model_validate(c) for c in message.pending_changes],
        created_at=message.created_at,
    )


@router.post("/{letter_id}/chat", response_model=ChatExchangeResponse)
async def cover_letter_chat(
    letter_id: UUID,
    body: ChatRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    letter = await _get_letter(db, letter_id, user.id)

    pending = await db.execute(
        select(CoverLetterPendingChange)
        .join(CoverLetterChatMessage)
        .where(
            CoverLetterChatMessage.cover_letter_id == letter_id,
            CoverLetterPendingChange.status == "pending",
        )
    )
    if pending.scalars().first():
        raise HTTPException(status_code=409, detail="Approve or reject pending changes first")

    user_msg = CoverLetterChatMessage(cover_letter_id=letter.id, role="user", content=body.message)
    db.add(user_msg)
    await db.flush()

    job_description = ""
    company_summary = ""
    if letter.resume_id:
        res = await db.execute(select(ResumeDocument).where(ResumeDocument.id == letter.resume_id))
        resume = res.scalar_one_or_none()
        if resume:
            job_description = resume.job_description or ""
            insights = resume.insights_json or {}
            company_summary = (insights.get("company_research") or {}).get("summary") or ""

    reply, changes = await run_cover_letter_agent(
        db, user.id, letter.content_json, body.message, job_description, company_summary
    )

    msg = CoverLetterChatMessage(cover_letter_id=letter.id, role="assistant", content=reply)
    db.add(msg)
    await db.flush()

    for ch in changes:
        db.add(
            CoverLetterPendingChange(
                message_id=msg.id,
                path=ch["path"],
                old_value=ch.get("old_value"),
                new_value=ch.get("new_value"),
                status="pending",
            )
        )
    await db.commit()
    result = await db.execute(
        select(CoverLetterChatMessage)
        .where(CoverLetterChatMessage.id.in_([user_msg.id, msg.id]))
        .options(selectinload(CoverLetterChatMessage.pending_changes))
        .order_by(CoverLetterChatMessage.created_at)
    )
    loaded = {m.id: m for m in result.scalars().all()}
    return ChatExchangeResponse(
        user_message=_cover_letter_chat_response(loaded[user_msg.id]),
        assistant_message=_cover_letter_chat_response(loaded[msg.id]),
    )


@router.post("/{letter_id}/changes")
async def handle_cover_letter_change(
    letter_id: UUID,
    body: ChangeActionRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    letter = await _get_letter(db, letter_id, user.id)
    result = await db.execute(
        select(CoverLetterPendingChange)
        .join(CoverLetterChatMessage)
        .where(
            CoverLetterPendingChange.id == body.change_id,
            CoverLetterChatMessage.cover_letter_id == letter_id,
        )
    )
    change = result.scalar_one_or_none()
    if not change:
        raise HTTPException(status_code=404, detail="Change not found")

    if body.action == "accept":
        letter.content_json = apply_change(letter.content_json, change.path, change.new_value or "")
        contact = await _get_contact(db, letter)
        letter.latex_source = render_cover_letter_latex(letter.content_json, contact)
        change.status = "accepted"
    else:
        change.status = "rejected"

    await db.commit()
    return {"ok": True, "content_json": letter.content_json}


@router.post("/{letter_id}/regenerate", response_model=CoverLetterResponse)
async def regenerate_cover_letter(
    letter_id: UUID,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _require_llm_config(db, user.id)
    letter = await _get_letter(db, letter_id, user.id)
    if letter.status == "processing":
        raise HTTPException(status_code=409, detail="Cover letter is still processing.")
    if not letter.resume_id:
        raise HTTPException(status_code=400, detail="Cover letter is not linked to a resume.")

    res = await db.execute(select(ResumeDocument).where(ResumeDocument.id == letter.resume_id))
    resume = res.scalar_one_or_none()
    if not resume or resume.user_id != user.id:
        raise HTTPException(status_code=404, detail="Linked resume not found")

    async def _run():
        from app.core.database import async_session

        async with async_session() as session:
            l_result = await session.execute(select(CoverLetterDocument).where(CoverLetterDocument.id == letter_id))
            l_doc = l_result.scalar_one()
            r_result = await session.execute(select(ResumeDocument).where(ResumeDocument.id == l_doc.resume_id))
            r_doc = r_result.scalar_one()
            await run_cover_letter_regeneration(session, l_doc, r_doc)

    letter.status = "processing"
    await db.commit()
    background_tasks.add_task(_run())
    await db.refresh(letter)
    return CoverLetterResponse.model_validate(letter)
