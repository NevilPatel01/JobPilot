from uuid import UUID

from sqlalchemy import select

from app.models.candidate import SENSITIVE_ANSWER_CATEGORIES, AnswerBankEntry
from app.schemas.candidate import AnswerBankEntryCreate, AnswerBankEntryUpdate
from app.services.audit import record_audit_event


async def create_answer_entry(db, user_id: UUID, data: AnswerBankEntryCreate) -> AnswerBankEntry:
    entry = AnswerBankEntry(
        user_id=user_id,
        question_text=data.question_text,
        question_category=data.question_category,
        answer_text=data.answer_text,
        related_fact_ids=data.related_fact_ids,
        # derived server-side; there is deliberately no client-settable field for this
        is_sensitive=data.question_category in SENSITIVE_ANSWER_CATEGORIES,
    )
    db.add(entry)
    await db.flush()
    await record_audit_event(
        db,
        user_id=user_id,
        action="answer_bank.created",
        entity_type="answer_bank_entries",
        entity_id=str(entry.id),
        after={"question_category": data.question_category, "is_sensitive": entry.is_sensitive},
    )
    return entry


async def list_answer_entries(db, user_id: UUID) -> list[AnswerBankEntry]:
    result = await db.execute(select(AnswerBankEntry).where(AnswerBankEntry.user_id == user_id))
    return result.scalars().all()


async def get_owned_answer_entry(db, user_id: UUID, entry_id: UUID) -> AnswerBankEntry | None:
    result = await db.execute(
        select(AnswerBankEntry).where(AnswerBankEntry.id == entry_id, AnswerBankEntry.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def update_answer_entry(db, user_id: UUID, entry_id: UUID, data: AnswerBankEntryUpdate) -> AnswerBankEntry | None:
    entry = await get_owned_answer_entry(db, user_id, entry_id)
    if not entry:
        return None
    for field in ("question_text", "question_category", "answer_text", "related_fact_ids"):
        value = getattr(data, field)
        if value is not None:
            setattr(entry, field, value)
    entry.is_sensitive = entry.question_category in SENSITIVE_ANSWER_CATEGORIES
    await db.flush()
    return entry


async def delete_answer_entry(db, user_id: UUID, entry_id: UUID) -> bool:
    entry = await get_owned_answer_entry(db, user_id, entry_id)
    if not entry:
        return False
    await db.delete(entry)
    await record_audit_event(
        db,
        user_id=user_id,
        action="answer_bank.deleted",
        entity_type="answer_bank_entries",
        entity_id=str(entry_id),
        before={"question_category": entry.question_category},
    )
    return True
