"""Persist user-accepted draft facts from any import source (resume text, GitHub).

Facts land unverified (the user still confirms each in the UI, per the
factuality rule). A project draft whose payload.url matches an existing active
project fact supersedes it instead of duplicating — re-syncs stay clean."""

from uuid import UUID

from app.schemas.candidate import CandidateFactCreate
from app.services.candidate.facts import create_fact, list_active_facts, supersede_fact


async def confirm_draft_facts(db, user_id: UUID, facts: list[dict]) -> dict:
    existing_projects = {
        (f.payload or {}).get("url"): f
        for f in await list_active_facts(db, user_id, fact_type="project", exclude_prohibited=False)
        if (f.payload or {}).get("url")
    }

    created = superseded = 0
    for raw in facts:
        draft = CandidateFactCreate.model_validate(raw)
        url = draft.payload.get("url") if draft.fact_type == "project" else None
        match = existing_projects.get(url) if url else None
        if match is not None:
            await supersede_fact(db, user_id, match.id, draft.payload, verification_status="unverified")
            superseded += 1
        else:
            await create_fact(db, user_id, draft)
            created += 1
    return {"created": created, "superseded": superseded}
