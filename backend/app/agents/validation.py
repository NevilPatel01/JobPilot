"""Validate LLM-tailored resume content against the user's source profile."""

from __future__ import annotations

import re

from app.schemas.resume_content import ResumeContent


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


def _safe_bullets(candidate: list[str], source: list[str]) -> bool:
    allowed_numbers = _numbers(" ".join(source))
    return all(_numbers(bullet).issubset(allowed_numbers) for bullet in candidate)


def guard_tailored_content(source: dict, tailored: dict) -> tuple[dict, list[str]]:
    """Strip invented employers/institutions; return cleaned content and warnings."""
    source_model = ResumeContent.model_validate(source or {})
    tailored_model = ResumeContent.model_validate(tailored or {})

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
        bullets = exp.bullets
        if not _safe_bullets(bullets, source_entry.bullets):
            bullets = list(source_entry.bullets)
            warnings.append(f"Reverted unsupported numeric claims in experience at '{source_entry.company}'.")
        cleaned_experience.append(
            source_entry.model_copy(update={"bullets": bullets})
        )

    cleaned_education = []
    source_by_institution = {_normalize(e.institution): e for e in source_model.education if e.institution}

    for edu in tailored_model.education:
        fallback = source_by_institution.get(_normalize(edu.institution))
        if not fallback or (edu.institution and not _fuzzy_match(edu.institution, allowed_institutions)):
            warnings.append(f"Removed invented institution '{edu.institution}' not found in your profile.")
            continue
        cleaned_education.append(fallback)

    allowed_skills = {
        _normalize(skill): skill
        for category in source_model.skills
        for skill in category.skills
        if skill
    }
    cleaned_skills = []
    for category in tailored_model.skills:
        kept = [allowed_skills[_normalize(skill)] for skill in category.skills if _normalize(skill) in allowed_skills]
        removed = [skill for skill in category.skills if _normalize(skill) not in allowed_skills]
        if removed:
            warnings.append(f"Removed skills not present in your profile: {', '.join(removed)}.")
        if kept:
            cleaned_skills.append(category.model_copy(update={"skills": list(dict.fromkeys(kept))}))

    source_projects_by_id = {project.id: project for project in source_model.projects}
    source_projects_by_name = {_normalize(project.name): project for project in source_model.projects if project.name}
    cleaned_projects = []
    for project in tailored_model.projects:
        source_project = source_projects_by_id.get(project.id) or source_projects_by_name.get(_normalize(project.name))
        if not source_project:
            warnings.append(f"Removed invented project '{project.name}' not found in your profile.")
            continue
        bullets = project.bullets
        if not _safe_bullets(bullets, source_project.bullets):
            bullets = list(source_project.bullets)
            warnings.append(f"Reverted unsupported numeric claims in project '{source_project.name}'.")
        cleaned_projects.append(source_project.model_copy(update={"bullets": bullets}))

    tailored_model.experience = cleaned_experience or list(source_model.experience)
    tailored_model.education = cleaned_education or list(source_model.education)
    tailored_model.projects = cleaned_projects or list(source_model.projects)
    tailored_model.skills = cleaned_skills or list(source_model.skills)
    tailored_model.contact = source_model.contact
    tailored_model.links = list(source_model.links)
    if not _numbers(tailored_model.summary).issubset(_numbers(source_model.summary)):
        tailored_model.summary = source_model.summary
        warnings.append("Reverted unsupported numeric claims in the tailored summary.")

    if warnings:
        warnings.insert(0, "Fact-check applied: tailored content must remain grounded in your profile.")

    return tailored_model.model_dump(), warnings
