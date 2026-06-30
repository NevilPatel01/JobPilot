from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agents.editor_agent import apply_change, run_editor_agent
from app.api.routes.resumes._helpers import (
    _ats_response,
    _chat_message_response,
    _get_resume,
)
from app.api.schemas import (
    ATSScoreResponse,
    BatchChangeActionRequest,
    ChangeActionRequest,
    ChatExchangeResponse,
    ChatMessageResponse,
    ChatRequest,
)
from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.resume import ChatMessage, PendingChange, ResumeDocument
from app.models.user import User
from app.services.ats.persist import save_ats_score
from app.services.resume.renderer import render_resume_latex

router = APIRouter()


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
    content = resume.content_json
    return ChatExchangeResponse(
        user_message=_chat_message_response(loaded[user_msg.id], content),
        assistant_message=_chat_message_response(loaded[msg.id], content),
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
