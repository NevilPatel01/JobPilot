from uuid import UUID

from sqlalchemy import select

from app.models.candidate import CandidateFact
from app.schemas.candidate import CandidateFactCreate, CandidateFactUpdate, validate_fact_payload
from app.services.audit import record_audit_event

# Verification-status transition adjacency, per docs/product/PHASE_1_IMPLEMENTATION_SPEC.md §9.
_ALLOWED_VERIFICATION_TRANSITIONS: dict[str, set[str]] = {
    "unverified": {"user_confirmed", "contradicted"},
    "user_confirmed": {"contradicted"},
    "contradicted": set(),  # only escapable via supersede_fact, not a direct status change
}


def is_valid_verification_transition(current: str, new: str) -> bool:
    return new in _ALLOWED_VERIFICATION_TRANSITIONS.get(current, set())


async def create_fact(db, user_id: UUID, data: CandidateFactCreate) -> CandidateFact:
    fact = CandidateFact(
        user_id=user_id,
        fact_type=data.fact_type,
        payload=data.payload,
        source=data.source,
        is_prohibited=data.is_prohibited,
        verification_status="user_confirmed" if data.source == "user_entered" else "unverified",
    )
    db.add(fact)
    await db.flush()
    await record_audit_event(
        db,
        user_id=user_id,
        action="candidate_fact.created",
        entity_type="candidate_facts",
        entity_id=str(fact.id),
        after=data.payload,
    )
    return fact


async def list_active_facts(
    db, user_id: UUID, fact_type: str | None = None, exclude_prohibited: bool = True,
) -> list[CandidateFact]:
    query = select(CandidateFact).where(
        CandidateFact.user_id == user_id, CandidateFact.superseded_by_id.is_(None)
    )
    if fact_type:
        query = query.where(CandidateFact.fact_type == fact_type)
    result = await db.execute(query)
    facts = result.scalars().all()
    if exclude_prohibited:
        facts = [f for f in facts if not f.is_prohibited]
    return facts


async def get_owned_fact(db, user_id: UUID, fact_id: UUID) -> CandidateFact | None:
    result = await db.execute(
        select(CandidateFact).where(CandidateFact.id == fact_id, CandidateFact.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def update_fact(db, user_id: UUID, fact_id: UUID, data: CandidateFactUpdate) -> CandidateFact | None:
    fact = await get_owned_fact(db, user_id, fact_id)
    if not fact:
        return None
    if data.payload is not None:
        fact.payload = validate_fact_payload(fact.fact_type, data.payload)
    if data.is_prohibited is not None:
        fact.is_prohibited = data.is_prohibited
    await db.flush()
    return fact


async def supersede_fact(db, user_id: UUID, fact_id: UUID, new_payload: dict) -> CandidateFact | None:
    old = await get_owned_fact(db, user_id, fact_id)
    if not old:
        return None
    new_fact = CandidateFact(
        user_id=user_id, fact_type=old.fact_type, payload=validate_fact_payload(old.fact_type, new_payload),
        source=old.source, verification_status="user_confirmed",
    )
    db.add(new_fact)
    await db.flush()
    old.superseded_by_id = new_fact.id
    await db.flush()
    await record_audit_event(
        db,
        user_id=user_id,
        action="candidate_fact.superseded",
        entity_type="candidate_facts",
        entity_id=str(new_fact.id),
        before=old.payload,
        after=new_fact.payload,
    )
    return new_fact


async def set_verification_status(db, user_id: UUID, fact_id: UUID, new_status: str) -> CandidateFact | None:
    fact = await get_owned_fact(db, user_id, fact_id)
    if not fact:
        return None
    if not is_valid_verification_transition(fact.verification_status, new_status):
        raise ValueError(f"invalid verification transition: {fact.verification_status} -> {new_status}")
    old_status = fact.verification_status
    fact.verification_status = new_status
    await db.flush()
    await record_audit_event(
        db,
        user_id=user_id,
        action="candidate_fact.verification_changed",
        entity_type="candidate_facts",
        entity_id=str(fact.id),
        before={"verification_status": old_status},
        after={"verification_status": new_status},
    )
    return fact
