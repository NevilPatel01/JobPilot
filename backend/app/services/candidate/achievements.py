from uuid import UUID

from sqlalchemy import select

from app.models.candidate import Achievement
from app.schemas.candidate import AchievementCreate, AchievementUpdate
from app.services.audit import record_audit_event
from app.services.candidate.facts import is_valid_verification_transition


async def create_achievement(db, user_id: UUID, data: AchievementCreate, source: str = "user_entered") -> Achievement:
    achievement = Achievement(
        user_id=user_id,
        related_fact_id=data.related_fact_id,
        situation=data.situation,
        task=data.task,
        action=data.action,
        result=data.result,
        metrics=data.metrics,
        tags=data.tags,
        source=source,
        verification_status="user_confirmed" if source == "user_entered" else "unverified",
    )
    db.add(achievement)
    await db.flush()
    await record_audit_event(
        db,
        user_id=user_id,
        action="achievement.created",
        entity_type="achievements",
        entity_id=str(achievement.id),
        after={"result": data.result, "tags": data.tags},
    )
    return achievement


async def list_achievements(db, user_id: UUID) -> list[Achievement]:
    result = await db.execute(select(Achievement).where(Achievement.user_id == user_id))
    return result.scalars().all()


async def get_owned_achievement(db, user_id: UUID, achievement_id: UUID) -> Achievement | None:
    result = await db.execute(
        select(Achievement).where(Achievement.id == achievement_id, Achievement.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def update_achievement(db, user_id: UUID, achievement_id: UUID, data: AchievementUpdate) -> Achievement | None:
    achievement = await get_owned_achievement(db, user_id, achievement_id)
    if not achievement:
        return None
    for field in ("related_fact_id", "situation", "task", "action", "result", "metrics", "tags"):
        value = getattr(data, field)
        if value is not None:
            setattr(achievement, field, value)
    await db.flush()
    return achievement


async def delete_achievement(db, user_id: UUID, achievement_id: UUID) -> bool:
    achievement = await get_owned_achievement(db, user_id, achievement_id)
    if not achievement:
        return False
    await db.delete(achievement)
    await record_audit_event(
        db,
        user_id=user_id,
        action="achievement.deleted",
        entity_type="achievements",
        entity_id=str(achievement_id),
        before={"result": achievement.result},
    )
    return True


async def set_achievement_verification(db, user_id: UUID, achievement_id: UUID, new_status: str) -> Achievement | None:
    achievement = await get_owned_achievement(db, user_id, achievement_id)
    if not achievement:
        return None
    if not is_valid_verification_transition(achievement.verification_status, new_status):
        raise ValueError(f"invalid verification transition: {achievement.verification_status} -> {new_status}")
    old_status = achievement.verification_status
    achievement.verification_status = new_status
    await db.flush()
    await record_audit_event(
        db,
        user_id=user_id,
        action="achievement.verification_changed",
        entity_type="achievements",
        entity_id=str(achievement.id),
        before={"verification_status": old_status},
        after={"verification_status": new_status},
    )
    return achievement
