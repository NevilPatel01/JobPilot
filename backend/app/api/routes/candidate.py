from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.schemas.candidate import (
    AchievementCreate,
    AchievementResponse,
    AchievementUpdate,
    AnswerBankEntryCreate,
    AnswerBankEntryResponse,
    AnswerBankEntryUpdate,
    CandidateFactCreate,
    CandidateFactResponse,
    CandidateFactUpdate,
    CareerProfileCreate,
    CareerProfileResponse,
    CareerProfileUpdate,
    SupersedeFactRequest,
)
from app.services.candidate.achievements import (
    create_achievement,
    delete_achievement,
    list_achievements,
    set_achievement_verification,
    update_achievement,
)
from app.services.candidate.answer_bank import (
    create_answer_entry,
    delete_answer_entry,
    list_answer_entries,
    update_answer_entry,
)
from app.services.candidate.career_profiles import (
    create_career_profile,
    delete_career_profile,
    list_career_profiles,
    set_default_career_profile,
    update_career_profile,
)
from app.services.candidate.facts import (
    create_fact,
    list_active_facts,
    set_verification_status,
    supersede_fact,
    update_fact,
)

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
    try:
        fact = await update_fact(db, user.id, fact_id, body)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc
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


@router.post("/facts/{fact_id}/supersede", response_model=CandidateFactResponse)
async def supersede_fact_route(
    fact_id: UUID,
    body: SupersedeFactRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_flag()
    try:
        fact = await supersede_fact(db, user.id, fact_id, body.payload)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc
    if not fact:
        raise HTTPException(status_code=404, detail="Fact not found")
    await db.commit()
    return CandidateFactResponse.model_validate(fact)


# --- achievements ---


@router.get("/achievements", response_model=list[AchievementResponse])
async def list_achievements_route(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_flag()
    rows = await list_achievements(db, user.id)
    return [AchievementResponse.model_validate(row) for row in rows]


@router.post("/achievements", response_model=AchievementResponse)
async def create_achievement_route(
    body: AchievementCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_flag()
    achievement = await create_achievement(db, user.id, body)
    await db.commit()
    return AchievementResponse.model_validate(achievement)


@router.patch("/achievements/{achievement_id}", response_model=AchievementResponse)
async def update_achievement_route(
    achievement_id: UUID,
    body: AchievementUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_flag()
    achievement = await update_achievement(db, user.id, achievement_id, body)
    if not achievement:
        raise HTTPException(status_code=404, detail="Achievement not found")
    await db.commit()
    return AchievementResponse.model_validate(achievement)


@router.delete("/achievements/{achievement_id}")
async def delete_achievement_route(
    achievement_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_flag()
    deleted = await delete_achievement(db, user.id, achievement_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Achievement not found")
    await db.commit()
    return {"deleted": True}


@router.post("/achievements/{achievement_id}/verify", response_model=AchievementResponse)
async def verify_achievement_route(
    achievement_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_flag()
    try:
        achievement = await set_achievement_verification(db, user.id, achievement_id, "user_confirmed")
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if not achievement:
        raise HTTPException(status_code=404, detail="Achievement not found")
    await db.commit()
    return AchievementResponse.model_validate(achievement)


# --- career profiles ---


@router.get("/career-profiles", response_model=list[CareerProfileResponse])
async def list_career_profiles_route(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_flag()
    rows = await list_career_profiles(db, user.id)
    return [CareerProfileResponse.model_validate(row) for row in rows]


@router.post("/career-profiles", response_model=CareerProfileResponse)
async def create_career_profile_route(
    body: CareerProfileCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_flag()
    profile = await create_career_profile(db, user.id, body)
    await db.commit()
    return CareerProfileResponse.model_validate(profile)


@router.patch("/career-profiles/{profile_id}", response_model=CareerProfileResponse)
async def update_career_profile_route(
    profile_id: UUID,
    body: CareerProfileUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_flag()
    profile = await update_career_profile(db, user.id, profile_id, body)
    if not profile:
        raise HTTPException(status_code=404, detail="Career profile not found")
    await db.commit()
    return CareerProfileResponse.model_validate(profile)


@router.delete("/career-profiles/{profile_id}")
async def delete_career_profile_route(
    profile_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_flag()
    deleted = await delete_career_profile(db, user.id, profile_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Career profile not found")
    await db.commit()
    return {"deleted": True}


@router.post("/career-profiles/{profile_id}/set-default", response_model=CareerProfileResponse)
async def set_default_career_profile_route(
    profile_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_flag()
    profile = await set_default_career_profile(db, user.id, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Career profile not found")
    await db.commit()
    return CareerProfileResponse.model_validate(profile)


# --- answer bank ---


@router.get("/answers", response_model=list[AnswerBankEntryResponse])
async def list_answers_route(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_flag()
    rows = await list_answer_entries(db, user.id)
    return [AnswerBankEntryResponse.model_validate(row) for row in rows]


@router.post("/answers", response_model=AnswerBankEntryResponse)
async def create_answer_route(
    body: AnswerBankEntryCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_flag()
    entry = await create_answer_entry(db, user.id, body)
    await db.commit()
    return AnswerBankEntryResponse.model_validate(entry)


@router.patch("/answers/{entry_id}", response_model=AnswerBankEntryResponse)
async def update_answer_route(
    entry_id: UUID,
    body: AnswerBankEntryUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_flag()
    entry = await update_answer_entry(db, user.id, entry_id, body)
    if not entry:
        raise HTTPException(status_code=404, detail="Answer not found")
    await db.commit()
    return AnswerBankEntryResponse.model_validate(entry)


@router.delete("/answers/{entry_id}")
async def delete_answer_route(
    entry_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_flag()
    deleted = await delete_answer_entry(db, user.id, entry_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Answer not found")
    await db.commit()
    return {"deleted": True}
