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


def guard_tailored_content(source: dict, tailored: dict) -> tuple[dict, list[str]]:
    """Strip invented employers/institutions; return cleaned content and warnings."""
    source_model = ResumeContent.model_validate(source or {})
    tailored_model = ResumeContent.model_validate(tailored or {})

    allowed_companies = {_normalize(e.company) for e in source_model.experience if e.company}
    allowed_institutions = {_normalize(e.institution) for e in source_model.education if e.institution}

    warnings: list[str] = []
    cleaned_experience = []
    source_by_company = {_normalize(e.company): e for e in source_model.experience if e.company}

    for exp in tailored_model.experience:
        if not exp.company or _fuzzy_match(exp.company, allowed_companies):
            cleaned_experience.append(exp)
            continue
        fallback = source_by_company.get(_normalize(exp.company))
        if fallback:
            cleaned_experience.append(fallback)
            warnings.append(f"Reverted experience at '{exp.company}' to source profile entry.")
        else:
            warnings.append(f"Removed invented employer '{exp.company}' not found in your profile.")

    cleaned_education = []
    source_by_institution = {_normalize(e.institution): e for e in source_model.education if e.institution}

    for edu in tailored_model.education:
        if not edu.institution or _fuzzy_match(edu.institution, allowed_institutions):
            cleaned_education.append(edu)
            continue
        fallback = source_by_institution.get(_normalize(edu.institution))
        if fallback:
            cleaned_education.append(fallback)
            warnings.append(f"Reverted education at '{edu.institution}' to source profile entry.")
        else:
            warnings.append(f"Removed invented institution '{edu.institution}' not found in your profile.")

    tailored_model.experience = cleaned_experience or list(source_model.experience)
    tailored_model.education = cleaned_education or list(source_model.education)

    if warnings:
        warnings.insert(0, "Fact-check applied: resume employers and schools must match your profile.")

    return tailored_model.model_dump(), warnings
