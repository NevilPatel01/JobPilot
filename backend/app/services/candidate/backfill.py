"""Idempotent backfill: legacy structured profile / user fields → unverified candidate facts.

Pure mapping lives in legacy_profile_to_draft_facts(); run_legacy_backfill() wraps
it with fetching + duplicate detection so it can run any number of times."""

import hashlib
import json
from datetime import date
from uuid import UUID

from sqlalchemy import select

from app.models.job_intelligence import UserScoringPrefs
from app.models.profile_structured import UserProfileStructured
from app.models.user import User
from app.schemas.candidate import CandidateFactCreate
from app.services.candidate.facts import create_fact, list_active_facts


def payload_hash(fact_type: str, payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(f"{fact_type}:{canonical}".encode()).hexdigest()


def _date_fields(payload: dict, raw: dict, fields: tuple[str, ...]) -> None:
    """Copy date fields when ISO-parseable; keep freeform values as *_text extras."""
    for field in fields:
        value = (raw.get(field) or "").strip()
        if not value:
            continue
        try:
            date.fromisoformat(value)
            payload[field] = value
        except ValueError:
            payload[f"{field}_text"] = value


def legacy_profile_to_draft_facts(
    content: dict, skills_keywords: list[str] | None, work_authorization: str | None,
) -> list[CandidateFactCreate]:
    drafts: list[CandidateFactCreate] = []

    contact = content.get("contact") or {}
    if any(str(v).strip() for v in contact.values()):
        drafts.append(CandidateFactCreate(fact_type="contact", payload=contact, source="inferred"))

    for entry in content.get("experience") or []:
        if not (entry.get("company") or "").strip() or not (entry.get("title") or "").strip():
            continue
        payload: dict = {
            "employer": entry["company"],
            "title": entry["title"],
            "summary": " ".join(entry.get("bullets") or []),
        }
        if (entry.get("location") or "").strip():
            payload["location"] = entry["location"]
        _date_fields(payload, entry, ("start_date", "end_date"))
        drafts.append(CandidateFactCreate(fact_type="employment", payload=payload, source="inferred"))

    for entry in content.get("education") or []:
        if not (entry.get("institution") or "").strip():
            continue
        payload = {"institution": entry["institution"], "credential": entry.get("degree") or ""}
        _date_fields(payload, entry, ("start_date", "end_date"))
        drafts.append(CandidateFactCreate(fact_type="education", payload=payload, source="inferred"))

    for entry in content.get("projects") or []:
        if not (entry.get("name") or "").strip():
            continue
        bullets = entry.get("bullets") or []
        payload = {
            "name": entry["name"],
            "url": entry.get("github_url") or entry.get("url") or "",
            "one_liner": bullets[0] if bullets else "",
            "highlights": bullets,
            "origin": "manual",
        }
        drafts.append(CandidateFactCreate(fact_type="project", payload=payload, source="inferred"))

    seen_skills: set[str] = set()
    skill_names: list[str] = []
    for category in content.get("skills") or []:
        skill_names.extend(category.get("skills") or [])
    skill_names.extend(skills_keywords or [])
    for name in skill_names:
        cleaned = (name or "").strip()
        if not cleaned or cleaned.casefold() in seen_skills:
            continue
        seen_skills.add(cleaned.casefold())
        drafts.append(CandidateFactCreate(fact_type="skill", payload={"name": cleaned}, source="inferred"))

    if work_authorization:
        drafts.append(
            CandidateFactCreate(
                fact_type="work_authorization",
                payload={"status": work_authorization, "country": "CA"},
                source="inferred",
            )
        )

    return drafts


async def run_legacy_backfill(db, user_id: UUID) -> dict:
    profile_row = (
        await db.execute(select(UserProfileStructured).where(UserProfileStructured.user_id == user_id))
    ).scalar_one_or_none()
    prefs = (
        await db.execute(select(UserScoringPrefs).where(UserScoringPrefs.user_id == user_id))
    ).scalar_one_or_none()
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()

    content = profile_row.content_json if profile_row else {}
    skills_keywords = list(user.skills_keywords or []) if user else []
    work_authorization = prefs.work_authorization if prefs else None

    drafts = legacy_profile_to_draft_facts(content or {}, skills_keywords, work_authorization)
    existing = await list_active_facts(db, user_id, exclude_prohibited=False)
    existing_hashes = {payload_hash(f.fact_type, f.payload) for f in existing}

    created = skipped = 0
    for draft in drafts:
        if payload_hash(draft.fact_type, draft.payload) in existing_hashes:
            skipped += 1
            continue
        await create_fact(db, user_id, draft)
        created += 1
    return {"created": created, "skipped": skipped}
