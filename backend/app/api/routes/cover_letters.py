from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.graph import run_cover_letter_regeneration
from app.api.schemas import CoverLetterListResponse, CoverLetterResponse, CoverLetterUpdate
from app.api.routes.resumes import _require_llm_config
from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.cover_letter import CoverLetterDocument
from app.models.resume import ResumeDocument
from app.models.user import User
from app.services.resume.renderer import render_cover_letter_html

router = APIRouter()


@router.get("", response_model=CoverLetterListResponse)
async def list_cover_letters(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CoverLetterDocument).where(CoverLetterDocument.user_id == user.id).order_by(CoverLetterDocument.updated_at.desc())
    )
    letters = result.scalars().all()
    return CoverLetterListResponse(cover_letters=[CoverLetterResponse.model_validate(cl) for cl in letters], total=len(letters))


@router.get("/{letter_id}", response_model=CoverLetterResponse)
async def get_cover_letter(
    letter_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    letter = await _get_letter(db, letter_id, user.id)
    return CoverLetterResponse.model_validate(letter)


async def _get_letter(db: AsyncSession, letter_id: UUID, user_id: UUID) -> CoverLetterDocument:
    result = await db.execute(
        select(CoverLetterDocument).where(CoverLetterDocument.id == letter_id, CoverLetterDocument.user_id == user_id)
    )
    letter = result.scalar_one_or_none()
    if not letter:
        raise HTTPException(status_code=404, detail="Cover letter not found")
    return letter


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
    if body.latex_source is not None:
        letter.latex_source = body.latex_source
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
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    letter = await _get_letter(db, letter_id, user.id)
    contact = {}
    if letter.resume_id:
        from app.models.resume import ResumeDocument

        res = await db.execute(select(ResumeDocument).where(ResumeDocument.id == letter.resume_id))
        resume = res.scalar_one_or_none()
        if resume:
            contact = resume.content_json.get("contact", {})
    return Response(content=render_cover_letter_html(letter.content_json, contact), media_type="text/html")


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
