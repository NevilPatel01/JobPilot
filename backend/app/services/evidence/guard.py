"""Field-level anti-fabrication guard for proposed single-path changes (editor chat agent).

Generalizes the same fact-checking rules agents/validation.py applies to full
tailored resumes (agents/validation.guard_tailored_content), scoped down to one
{path, new_value} pair at a time so the editor chat agent can guard each
proposed diff before it becomes a PendingChange.
"""

from __future__ import annotations

import re
from typing import Any

_NUMBER_RE = re.compile(r"\b\d+(?:\.\d+)?(?:%|[kKmMbB])?\b")


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()


def _fuzzy_match(candidate: str, allowed: set[str]) -> bool:
    norm = _normalize(candidate)
    if not norm:
        return True
    if norm in allowed:
        return True
    return any(item and (norm in item or item in norm) for item in allowed)


def _numbers(value: str) -> set[str]:
    return set(_NUMBER_RE.findall(value or ""))


def extract_guard_context(content: dict) -> dict:
    """Derive the allow-lists a guard_proposed_change call needs from the
    ResumeContent-shaped dict currently loaded in the editor."""
    experience = content.get("experience") or []
    education = content.get("education") or []
    all_bullets = []
    for entry in experience:
        all_bullets.extend(entry.get("bullets") or [])
    for entry in (content.get("projects") or []):
        all_bullets.extend(entry.get("bullets") or [])
    summary = content.get("summary") or ""

    return {
        "allowed_company_names": {_normalize(e.get("company", "")) for e in experience if e.get("company")},
        "allowed_institution_names": {_normalize(e.get("institution", "")) for e in education if e.get("institution")},
        "allowed_numbers": _numbers(" ".join(all_bullets) + " " + summary),
    }


def _is_bullet_path(path: str) -> bool:
    return ".bullets[" in path or path.endswith(".bullets")


def _is_company_path(path: str) -> bool:
    return path.endswith(".company")


def _is_institution_path(path: str) -> bool:
    return path.endswith(".institution")


def _is_skills_path(path: str) -> bool:
    return "skills" in path


def guard_proposed_change(
    path: str,
    proposed_value: Any,
    *,
    allowed_company_names: set[str],
    allowed_institution_names: set[str],
    allowed_numbers: set[str],
) -> tuple[Any, str | None]:
    """Returns (value_to_use, warning_or_None). Skills paths are always allowed
    through unchanged (matches agents/validation.py's deliberate skills exception)."""
    if _is_skills_path(path):
        return proposed_value, None

    if _is_company_path(path) and isinstance(proposed_value, str):
        if not _fuzzy_match(proposed_value, allowed_company_names):
            return None, f"Rejected invented employer '{proposed_value}' not found in your profile."
        return proposed_value, None

    if _is_institution_path(path) and isinstance(proposed_value, str):
        if not _fuzzy_match(proposed_value, allowed_institution_names):
            return None, f"Rejected invented institution '{proposed_value}' not found in your profile."
        return proposed_value, None

    if _is_bullet_path(path):
        if isinstance(proposed_value, str):
            if not _numbers(proposed_value).issubset(allowed_numbers):
                return None, "Rejected an unsupported number in this bullet."
            return proposed_value, None
        if isinstance(proposed_value, list):
            bad = [b for b in proposed_value if not _numbers(b).issubset(allowed_numbers)]
            if bad:
                return None, "Rejected an unsupported number in one of these bullets."
            return proposed_value, None

    if path == "summary" and isinstance(proposed_value, str):
        if not _numbers(proposed_value).issubset(allowed_numbers):
            return None, "Rejected an unsupported number in the summary."
        return proposed_value, None

    return proposed_value, None
