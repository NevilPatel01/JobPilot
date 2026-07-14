from uuid import UUID

from sqlalchemy import select

from app.models.candidate import CareerProfile
from app.schemas.candidate import CareerProfileCreate, CareerProfileUpdate
from app.services.audit import record_audit_event


async def _clear_other_defaults(db, user_id: UUID, keep_id: UUID | None = None) -> None:
    result = await db.execute(
        select(CareerProfile).where(CareerProfile.user_id == user_id, CareerProfile.is_default.is_(True))
    )
    for profile in result.scalars().all():
        if keep_id is None or profile.id != keep_id:
            profile.is_default = False


async def create_career_profile(db, user_id: UUID, data: CareerProfileCreate) -> CareerProfile:
    if data.is_default:
        await _clear_other_defaults(db, user_id)
    profile = CareerProfile(
        user_id=user_id,
        name=data.name,
        description=data.description,
        emphasis_fact_ids=data.emphasis_fact_ids,
        positioning_statement=data.positioning_statement,
        is_default=data.is_default,
    )
    db.add(profile)
    await db.flush()
    await record_audit_event(
        db,
        user_id=user_id,
        action="career_profile.created",
        entity_type="career_profiles",
        entity_id=str(profile.id),
        after={"name": data.name, "is_default": data.is_default},
    )
    return profile


async def list_career_profiles(db, user_id: UUID) -> list[CareerProfile]:
    result = await db.execute(select(CareerProfile).where(CareerProfile.user_id == user_id))
    return result.scalars().all()


async def get_owned_career_profile(db, user_id: UUID, profile_id: UUID) -> CareerProfile | None:
    result = await db.execute(
        select(CareerProfile).where(CareerProfile.id == profile_id, CareerProfile.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def update_career_profile(db, user_id: UUID, profile_id: UUID, data: CareerProfileUpdate) -> CareerProfile | None:
    profile = await get_owned_career_profile(db, user_id, profile_id)
    if not profile:
        return None
    for field in ("name", "description", "emphasis_fact_ids", "positioning_statement"):
        value = getattr(data, field)
        if value is not None:
            setattr(profile, field, value)
    await db.flush()
    return profile


async def delete_career_profile(db, user_id: UUID, profile_id: UUID) -> bool:
    profile = await get_owned_career_profile(db, user_id, profile_id)
    if not profile:
        return False
    await db.delete(profile)
    await record_audit_event(
        db,
        user_id=user_id,
        action="career_profile.deleted",
        entity_type="career_profiles",
        entity_id=str(profile_id),
        before={"name": profile.name},
    )
    return True


async def set_default_career_profile(db, user_id: UUID, profile_id: UUID) -> CareerProfile | None:
    profile = await get_owned_career_profile(db, user_id, profile_id)
    if not profile:
        return None
    await _clear_other_defaults(db, user_id, keep_id=profile.id)
    profile.is_default = True
    await db.flush()
    await record_audit_event(
        db,
        user_id=user_id,
        action="career_profile.default_changed",
        entity_type="career_profiles",
        entity_id=str(profile.id),
        after={"is_default": True},
    )
    return profile
