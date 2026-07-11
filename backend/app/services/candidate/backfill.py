"""Derive an initial set of candidate_facts from an existing ResumeContent-shaped
profile (user_profiles_structured.content_json), per
docs/product/PHASE_1_IMPLEMENTATION_SPEC.md §11/§12. Existing profile data is
treated as already candidate-affirmed (not unverified) since the user put it
there deliberately — backfill_facts_from_profile below overrides the
verification_status to user_confirmed after create_fact() runs, rather than
changing create_fact()'s general "resume_upload" default (which should stay
unverified for a fresh, not-yet-reviewed PDF re-parse in the future)."""

from uuid import UUID

from app.schemas.candidate import CandidateFactCreate
from app.services.candidate.facts import create_fact, list_active_facts, set_verification_status


def backfill_facts_from_content(content: dict) -> list[CandidateFactCreate]:
    facts: list[CandidateFactCreate] = []

    contact = content.get("contact", {})
    if contact.get("full_name") or contact.get("location"):
        facts.append(CandidateFactCreate(
            fact_type="personal",
            payload={"full_name": contact.get("full_name", ""), "location": contact.get("location", "")},
            source="resume_upload",
        ))
    if contact.get("email") or contact.get("phone"):
        facts.append(CandidateFactCreate(
            fact_type="contact",
            payload={"email": contact.get("email", ""), "phone": contact.get("phone", "")},
            source="resume_upload",
        ))

    for entry in content.get("experience", []):
        facts.append(CandidateFactCreate(fact_type="employment", payload=dict(entry), source="resume_upload"))

    for entry in content.get("education", []):
        facts.append(CandidateFactCreate(fact_type="education", payload=dict(entry), source="resume_upload"))

    for entry in content.get("projects", []):
        facts.append(CandidateFactCreate(fact_type="project", payload=dict(entry), source="resume_upload"))

    for category in content.get("skills", []):
        facts.append(CandidateFactCreate(
            fact_type="skill",
            payload={"category": category.get("name", ""), "skills": category.get("skills", [])},
            source="resume_upload",
        ))

    return facts


async def backfill_facts_from_profile(db, user_id: UUID, force: bool = False) -> dict:
    if not force:
        existing = await list_active_facts(db, user_id, exclude_prohibited=False)
        if existing:
            return {"facts_created": 0, "skipped": True}

    from app.models.profile_structured import UserProfileStructured
    from sqlalchemy import select

    result = await db.execute(select(UserProfileStructured).where(UserProfileStructured.user_id == user_id))
    row = result.scalar_one_or_none()
    if not row or not row.content_json:
        return {"facts_created": 0, "skipped": True}

    created = 0
    for fact_data in backfill_facts_from_content(row.content_json):
        fact = await create_fact(db, user_id, fact_data)
        # Backfilled facts represent data the candidate already affirmed by
        # putting it in their profile — mark them user_confirmed, per the
        # documented trust decision above, rather than leaving them unverified.
        await set_verification_status(db, user_id, fact.id, "user_confirmed")
        created += 1

    await db.commit()
    return {"facts_created": created, "skipped": False}
