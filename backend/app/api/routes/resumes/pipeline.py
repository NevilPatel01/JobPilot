from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.resumes._helpers import (
    _ats_response,
    _ensure_not_processing,
    _get_resume,
    _pipeline_task,
    _require_llm_config,
    _resume_response,
)
from app.api.schemas import ATSScoreHistoryResponse, ATSScoreResponse, ResumeResponse
from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.resume import ATSScore
from app.models.user import User
from app.services.ats.persist import save_ats_score

router = APIRouter()


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
    aggressive: bool = Query(False, description="Aggressively rewrite bullets to match the JD and add role-standard keywords"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _require_llm_config(db, user.id)
    resume = await _get_resume(db, resume_id, user.id)
    await _ensure_not_processing(resume)
    background_tasks.add_task(_pipeline_task(resume.id, "tailor_only", aggressive=aggressive))
    resume.status = "processing"
    await db.commit()
    await db.refresh(resume)
    return _resume_response(resume)
