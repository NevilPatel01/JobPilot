"""Validate LLM-tailored resume content against the user's source profile.

Anti-fabrication guardrails, tuned to still allow meaningful ATS optimization:
  - Employers, institutions, and projects must exist in the source profile.
  - Numeric metrics may not be invented (guarded per-bullet, not per-entry, so
    one bad number doesn't wipe out a whole entry's tailoring).
  - Skills MAY be added (rephrased/implied JD keywords) — this is required to
    lift ATS keyword coverage — but employers/dates/titles stay exactly as the
    user wrote them.
"""

from __future__ import annotations

import re

from app.schemas.resume_content import ResumeContent

MAX_SKILLS_PER_CATEGORY = 30


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()


def _fuzzy_match(candidate: str, allowed: set[str]) -> bool:
    norm = _normalize(candidate)
    if not norm:
        return True
    if norm in allowed:
        return True
    for item in allowed:
        if not item:
            continue
        if norm in item or item in norm:
            return True
    return False


def _numbers(value: str) -> set[str]:
    return set(re.findall(r"\b\d+(?:\.\d+)?(?:%|[kKmMbB])?\b", value or ""))


def _guard_bullets(tailored: list[str], source: list[str]) -> tuple[list[str], bool]:
    """Keep tailored (reworded) bullets, but swap out any bullet that invents a
    number for the source bullet at the same position. Only the offending
    bullet is reverted — the rest of the tailoring is preserved."""
    allowed = _numbers(" ".join(source or []))
    out: list[str] = []
    reverted = False
    for i, bullet in enumerate(tailored or []):
        if not (bullet or "").strip():
            continue
        if _numbers(bullet).issubset(allowed):
            out.append(bullet)
        elif i < len(source or []):
            out.append(source[i])
            reverted = True
        else:
            reverted = True  # fabricated-number bullet with no counterpart — drop
    if not out:
        out = [b for b in (source or []) if b]
    return out, reverted


def _prohibited_hit(value: str, prohibited_terms: set[str]) -> bool:
    norm = _normalize(value)
    return bool(norm) and any(term and term in norm for term in prohibited_terms)


def guard_tailored_content(
    source: dict, tailored: dict, facts_guard: dict | None = None,
) -> tuple[dict, list[str]]:
    """Strip invented employers/institutions/projects and fabricated metrics;
    keep reworded bullets and added skills. Returns cleaned content + warnings.

    facts_guard (facts-based resumes only):
      {"confirmed_project_fact_ids": [...], "prohibited_terms": [...]}
    Projects must carry an evidence_fact_id from the confirmed set; content
    matching a prohibited term is removed even if it exists in the source."""
    source_model = ResumeContent.model_validate(source or {})
    tailored_model = ResumeContent.model_validate(tailored or {})

    confirmed_project_ids = set((facts_guard or {}).get("confirmed_project_fact_ids") or [])
    prohibited_terms = {_normalize(t) for t in (facts_guard or {}).get("prohibited_terms") or [] if _normalize(t)}
    facts_mode = facts_guard is not None

    allowed_companies = {_normalize(e.company) for e in source_model.experience if e.company}
    allowed_institutions = {_normalize(e.institution) for e in source_model.education if e.institution}

    warnings: list[str] = []
    cleaned_experience = []
    source_by_company = {_normalize(e.company): e for e in source_model.experience if e.company}
    source_by_id = {e.id: e for e in source_model.experience}

    for exp in tailored_model.experience:
        source_entry = source_by_id.get(exp.id) or source_by_company.get(_normalize(exp.company))
        if not source_entry or (exp.company and not _fuzzy_match(exp.company, allowed_companies)):
            warnings.append(f"Removed invented employer '{exp.company}' not found in your profile.")
            continue
        if prohibited_terms and (
            _prohibited_hit(exp.company, prohibited_terms) or _prohibited_hit(exp.title, prohibited_terms)
        ):
            warnings.append(f"Removed experience at '{exp.company}' — matches a prohibited claim.")
            continue
        bullets, reverted = _guard_bullets(exp.bullets, source_entry.bullets)
        if reverted:
            warnings.append(f"Removed an unsupported number in experience at '{source_entry.company}'.")
        # Keep the user's real title/company/location/dates; use the tailored bullets.
        cleaned_experience.append(source_entry.model_copy(update={"bullets": bullets}))

    cleaned_education = []
    source_by_institution = {_normalize(e.institution): e for e in source_model.education if e.institution}
    for edu in tailored_model.education:
        fallback = source_by_institution.get(_normalize(edu.institution))
        if not fallback or (edu.institution and not _fuzzy_match(edu.institution, allowed_institutions)):
            warnings.append(f"Removed invented institution '{edu.institution}' not found in your profile.")
            continue
        cleaned_education.append(fallback)

    # Skills: ALLOW additions (implied / JD keywords). Only dedupe and cap.
    cleaned_skills = []
    for category in tailored_model.skills:
        seen: set[str] = set()
        deduped: list[str] = []
        for skill in category.skills:
            key = _normalize(skill)
            if prohibited_terms and _prohibited_hit(skill, prohibited_terms):
                warnings.append(f"Removed prohibited skill claim '{skill.strip()}'.")
                continue
            if key and key not in seen:
                seen.add(key)
                deduped.append(skill.strip())
        if deduped:
            cleaned_skills.append(category.model_copy(update={"skills": deduped[:MAX_SKILLS_PER_CATEGORY]}))

    source_projects_by_id = {p.id: p for p in source_model.projects}
    source_projects_by_name = {_normalize(p.name): p for p in source_model.projects if p.name}
    cleaned_projects = []
    for project in tailored_model.projects:
        source_project = source_projects_by_id.get(project.id) or source_projects_by_name.get(_normalize(project.name))
        if not source_project:
            warnings.append(f"Removed invented project '{project.name}' not found in your profile.")
            continue
        if facts_mode:
            evidence_id = project.evidence_fact_id or source_project.evidence_fact_id
            if evidence_id not in confirmed_project_ids:
                warnings.append(f"Removed project '{project.name}' — not backed by a confirmed candidate fact.")
                continue
            if prohibited_terms and _prohibited_hit(project.name, prohibited_terms):
                warnings.append(f"Removed project '{project.name}' — matches a prohibited claim.")
                continue
        bullets, reverted = _guard_bullets(project.bullets, source_project.bullets)
        if reverted:
            warnings.append(f"Removed an unsupported number in project '{source_project.name}'.")
        cleaned_projects.append(source_project.model_copy(update={"bullets": bullets}))

    if facts_mode:
        # facts mode: an empty section is a legitimate guard outcome — restoring
        # the source here would resurrect exactly what was removed
        tailored_model.experience = cleaned_experience
        tailored_model.education = cleaned_education or list(source_model.education)
        tailored_model.projects = cleaned_projects
        tailored_model.skills = cleaned_skills
    else:
        tailored_model.experience = cleaned_experience or list(source_model.experience)
        tailored_model.education = cleaned_education or list(source_model.education)
        tailored_model.projects = cleaned_projects or list(source_model.projects)
        tailored_model.skills = cleaned_skills or list(source_model.skills)
    tailored_model.contact = source_model.contact
    tailored_model.links = list(source_model.links)
    if not _numbers(tailored_model.summary).issubset(_numbers(source_model.summary)):
        tailored_model.summary = source_model.summary
        warnings.append("Reverted an unsupported number in the tailored summary.")

    if warnings:
        warnings.insert(0, "Fact-check applied: employers, dates, and metrics stay true to your profile.")

    return tailored_model.model_dump(), warnings
