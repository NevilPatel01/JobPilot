"""Facts → scorer inputs and facts → ResumeContent adapters (flag-gated consumers).

Scoring may use unverified-but-not-contradicted facts (internal signal);
the resume builder uses ONLY user-confirmed facts (factuality rule)."""

from dataclasses import dataclass
from datetime import date, datetime, timezone
from uuid import UUID

from app.models.candidate import CandidateFact
from app.services.candidate.facts import list_active_facts


@dataclass(frozen=True)
class FactsCandidateInputs:
    skills: tuple[str, ...]
    years_experience: float | None
    work_authorization: str | None


def _usable(fact: CandidateFact) -> bool:
    return fact.verification_status != "contradicted"


def _confirmed(fact: CandidateFact) -> bool:
    return fact.verification_status == "user_confirmed"


def _parse_iso(value) -> date | None:
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def _employment_years(employment_payloads: list[dict]) -> float | None:
    today = datetime.now(timezone.utc).date()
    total_months = 0
    for payload in employment_payloads:
        start = _parse_iso(payload.get("start_date"))
        if not start:
            continue
        end = _parse_iso(payload.get("end_date")) or today
        if end >= start:
            total_months += max(6, (end.year - start.year) * 12 + (end.month - start.month))
    return round(min(total_months / 12, 40), 1) if total_months else None


async def facts_candidate_inputs(db, user_id: UUID) -> FactsCandidateInputs | None:
    facts = [f for f in await list_active_facts(db, user_id) if _usable(f)]
    skills = tuple(
        dict.fromkeys(
            str((f.payload or {}).get("name") or "").strip()
            for f in facts
            if f.fact_type == "skill" and str((f.payload or {}).get("name") or "").strip()
        )
    )
    employment = [f.payload or {} for f in facts if f.fact_type == "employment"]
    if not skills and not employment:
        return None
    auth_facts = [f for f in facts if f.fact_type == "work_authorization"]
    work_authorization = (auth_facts[0].payload or {}).get("status") if auth_facts else None
    return FactsCandidateInputs(
        skills=skills,
        years_experience=_employment_years(employment),
        work_authorization=work_authorization,
    )


def _split_bullets(summary: str) -> list[str]:
    return [s.strip().rstrip(".") for s in (summary or "").split(". ") if s.strip()]


def _project_fact_dict(fact: CandidateFact) -> dict:
    payload = fact.payload or {}
    return {
        "fact_id": str(fact.id),
        "name": payload.get("name") or "",
        "url": payload.get("url") or "",
        "one_liner": payload.get("one_liner") or "",
        "highlights": payload.get("highlights") or [],
        "tech_stack": payload.get("tech_stack") or [],
        "stars": int(payload.get("stars") or 0),
        "pinned": bool(payload.get("pinned")),
    }


def project_fact_to_entry(project: dict) -> dict:
    bullets = [b for b in [project.get("one_liner", "").strip(), *project.get("highlights", [])] if b]
    return {
        "name": project["name"],
        "github_url": project["url"],
        "bullets": bullets[:3],
        "evidence_fact_id": project["fact_id"],
    }


async def build_resume_content_from_facts(db, user_id: UUID) -> tuple[dict | None, list[dict]]:
    """ResumeContent-shaped dict from user-confirmed facts, plus the compact
    project-fact dicts the tailor step re-selects per job."""
    facts = [f for f in await list_active_facts(db, user_id) if _confirmed(f)]
    by_type: dict[str, list[CandidateFact]] = {}
    for fact in facts:
        by_type.setdefault(fact.fact_type, []).append(fact)

    if not any(by_type.get(t) for t in ("employment", "education", "skill", "project")):
        return None, []

    contact_payload = (by_type.get("contact") or [CandidateFact(payload={})])[0].payload or {}
    contact = {
        "full_name": contact_payload.get("full_name") or contact_payload.get("name") or "",
        "email": contact_payload.get("email") or "",
        "phone": contact_payload.get("phone") or "",
        "location": contact_payload.get("location") or "",
    }

    experience = [
        {
            "company": p.get("employer") or "",
            "title": p.get("title") or "",
            "location": p.get("location") or "",
            "start_date": str(p.get("start_date") or p.get("start_date_text") or ""),
            "end_date": str(p.get("end_date") or p.get("end_date_text") or ""),
            "bullets": _split_bullets(p.get("summary") or ""),
        }
        for p in ((f.payload or {}) for f in by_type.get("employment") or [])
    ]
    education = [
        {
            "institution": p.get("institution") or "",
            "degree": p.get("credential") or "",
            "start_date": str(p.get("start_date") or ""),
            "end_date": str(p.get("end_date") or ""),
        }
        for p in ((f.payload or {}) for f in by_type.get("education") or [])
    ]
    skill_names = [
        str((f.payload or {}).get("name") or "").strip()
        for f in by_type.get("skill") or []
        if str((f.payload or {}).get("name") or "").strip()
    ]
    skills = [{"name": "Skills", "skills": list(dict.fromkeys(skill_names))}] if skill_names else []

    project_facts = sorted(
        (_project_fact_dict(f) for f in by_type.get("project") or []),
        key=lambda p: (not p["pinned"], -p["stars"], p["name"].casefold()),
    )
    # default (no JD yet): top 2 — the tailor step re-selects seniority-adaptively
    projects = [project_fact_to_entry(p) for p in project_facts[:2]]

    content = {
        "contact": contact,
        "summary": "",
        "experience": experience,
        "education": education,
        "skills": skills,
        "projects": projects,
    }
    return content, project_facts
