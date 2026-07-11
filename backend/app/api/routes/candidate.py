from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.schemas.candidate import CandidateFactCreate, CandidateFactResponse, CandidateFactUpdate
from app.services.candidate.facts import create_fact, list_active_facts, set_verification_status, update_fact

router = APIRouter()


def _require_flag() -> None:
    if not settings.feature_candidate_intelligence:
        raise HTTPException(status_code=404, detail="Not found")


@router.get("/facts", response_model=list[CandidateFactResponse])
async def list_facts(
    fact_type: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_flag()
    facts = await list_active_facts(db, user.id, fact_type=fact_type)
    return [CandidateFactResponse.model_validate(f) for f in facts]


@router.post("/facts", response_model=CandidateFactResponse)
async def create_fact_route(
    body: CandidateFactCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_flag()
    fact = await create_fact(db, user.id, body)
    await db.commit()
    return CandidateFactResponse.model_validate(fact)


@router.patch("/facts/{fact_id}", response_model=CandidateFactResponse)
async def update_fact_route(
    fact_id: UUID,
    body: CandidateFactUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_flag()
    fact = await update_fact(db, user.id, fact_id, body)
    if not fact:
        raise HTTPException(status_code=404, detail="Fact not found")
    await db.commit()
    return CandidateFactResponse.model_validate(fact)


@router.post("/facts/{fact_id}/verify", response_model=CandidateFactResponse)
async def verify_fact_route(
    fact_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_flag()
    try:
        fact = await set_verification_status(db, user.id, fact_id, "user_confirmed")
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if not fact:
        raise HTTPException(status_code=404, detail="Fact not found")
    await db.commit()
    return CandidateFactResponse.model_validate(fact)


@router.post("/facts/{fact_id}/dispute", response_model=CandidateFactResponse)
async def dispute_fact_route(
    fact_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_flag()
    try:
        fact = await set_verification_status(db, user.id, fact_id, "contradicted")
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if not fact:
        raise HTTPException(status_code=404, detail="Fact not found")
    await db.commit()
    return CandidateFactResponse.model_validate(fact)
