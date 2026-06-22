from copy import deepcopy
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.jobs.scoring.categories import CATEGORY_KEYWORDS, CATEGORY_LABELS
from app.models.job_intelligence import ResumeCategoryTemplate
from app.models.profile_structured import UserProfileStructured
from app.schemas.resume_content import ResumeContent


RESUME_CATEGORIES = tuple(CATEGORY_LABELS)


def _relevance(text: str, keywords: set[str]) -> int:
    normalized = text.casefold()
    return sum(1 for keyword in keywords if keyword in normalized)


def build_category_template(profile_content: dict[str, Any], category: str) -> tuple[dict, dict]:
    if category not in CATEGORY_KEYWORDS:
        raise ValueError(f"Unsupported resume category: {category}")
    # Validation and a deep copy ensure the source profile is never mutated.
    content = ResumeContent.model_validate(deepcopy(profile_content)).model_dump()
    keywords = CATEGORY_KEYWORDS[category]

    promoted_skills: list[str] = []
    for skill_group in content["skills"]:
        skill_group["skills"] = sorted(
            skill_group["skills"],
            key=lambda skill: (_relevance(skill, keywords), skill.casefold()),
            reverse=True,
        )
        promoted_skills.extend(skill for skill in skill_group["skills"] if _relevance(skill, keywords))
    content["skills"] = sorted(
        content["skills"],
        key=lambda group: _relevance(f"{group['name']} {' '.join(group['skills'])}", keywords),
        reverse=True,
    )

    def entry_score(entry: dict) -> int:
        return _relevance(" ".join(str(value) for value in entry.values()), keywords)

    content["experience"] = sorted(content["experience"], key=entry_score, reverse=True)
    content["projects"] = sorted(content["projects"], key=entry_score, reverse=True)
    relevant_experience = [entry["id"] for entry in content["experience"] if entry_score(entry)]
    relevant_projects = [entry["id"] for entry in content["projects"] if entry_score(entry)]

    notes = {
        "category": category,
        "category_label": CATEGORY_LABELS[category],
        "promoted_skills": list(dict.fromkeys(promoted_skills)),
        "relevant_experience_ids": relevant_experience,
        "relevant_project_ids": relevant_projects,
        "truthfulness": "Reordered existing profile content only; no experience, skills, or claims were added.",
    }
    return content, notes


def profile_has_substance(content: dict[str, Any]) -> bool:
    validated = ResumeContent.model_validate(content)
    return bool(validated.summary.strip() or validated.experience or validated.projects or validated.skills)


async def _get_profile(session: AsyncSession, user_id: UUID) -> UserProfileStructured | None:
    result = await session.execute(
        select(UserProfileStructured).where(UserProfileStructured.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def ensure_resume_template(
    session: AsyncSession,
    user_id: UUID,
    category: str,
) -> ResumeCategoryTemplate:
    if category not in RESUME_CATEGORIES:
        raise ValueError(f"Unsupported resume category: {category}")
    profile = await _get_profile(session, user_id)
    if not profile or not profile_has_substance(profile.content_json):
        raise ValueError("Complete your structured profile before generating a tailored resume")
    result = await session.execute(
        select(ResumeCategoryTemplate).where(
            ResumeCategoryTemplate.user_id == user_id,
            ResumeCategoryTemplate.category == category,
        )
    )
    template = result.scalar_one_or_none()
    profile_updated_at = profile.updated_at or datetime.now(timezone.utc)
    if not template:
        template = ResumeCategoryTemplate(user_id=user_id, category=category)
        session.add(template)
    if not template.base_content or template.generated_from_profile_at != profile_updated_at:
        content, notes = build_category_template(profile.content_json, category)
        template.base_content = content
        template.selection_notes = notes
        template.generated_from_profile_at = profile_updated_at
        await session.flush()
    return template


async def seed_resume_templates(session: AsyncSession, user_id: UUID) -> list[ResumeCategoryTemplate]:
    templates = [await ensure_resume_template(session, user_id, category) for category in RESUME_CATEGORIES]
    return templates
