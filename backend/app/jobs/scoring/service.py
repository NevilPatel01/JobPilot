import re
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.jobs.scoring.engine import CandidateProfile, JobFacts, score_job
from app.models.job import Job
from app.models.job_intelligence import InboxJob, JobFitScore, UserScoringPrefs
from app.models.profile_structured import UserProfileStructured
from app.models.user import User


def _profile_experience_years(content: dict) -> float | None:
    total_months = 0
    current_year = datetime.now(timezone.utc).year
    for experience in content.get("experience", []):
        start_match = re.search(r"\b(19|20)\d{2}\b", str(experience.get("start_date", "")))
        if not start_match:
            continue
        end_text = str(experience.get("end_date", ""))
        end_match = re.search(r"\b(19|20)\d{2}\b", end_text)
        start_year = int(start_match.group())
        end_year = int(end_match.group()) if end_match else current_year
        if start_year <= end_year <= current_year + 1:
            total_months += max(6, (end_year - start_year) * 12)
    return round(min(total_months / 12, 40), 1) if total_months else None


def _profile_skills(user: User, content: dict) -> tuple[str, ...]:
    skills = list(user.skills_keywords or [])
    for category in content.get("skills", []):
        skills.extend(category.get("skills", []))
    return tuple(dict.fromkeys(str(skill).strip() for skill in skills if str(skill).strip()))


async def build_candidate_profile(
    session: AsyncSession,
    user: User,
    prefs: UserScoringPrefs | None = None,
) -> CandidateProfile:
    if prefs is None:
        prefs = await session.get(UserScoringPrefs, user.id)
    profile_result = await session.execute(
        select(UserProfileStructured).where(UserProfileStructured.user_id == user.id)
    )
    structured = profile_result.scalar_one_or_none()
    content = structured.content_json if structured else {}
    years = _profile_experience_years(content)
    if years is None and user.resume_text:
        match = re.search(r"\b(\d{1,2})\+?\s+years?\b", user.resume_text, re.IGNORECASE)
        years = float(match.group(1)) if match else None
    return CandidateProfile(
        skills=_profile_skills(user, content),
        years_experience=years,
        work_authorization=prefs.work_authorization if prefs else "work_permit",
        target_provinces=tuple(prefs.target_provinces) if prefs else ("AB", "BC", "ON", "SK"),
        relocation_open=prefs.relocation_open if prefs else True,
    )


def _job_facts(job: Job) -> JobFacts:
    return JobFacts(
        title=job.title,
        company=job.company,
        description=job.description or "",
        skills=tuple(job.skills or job.tech_stack or []),
        requirements=tuple(job.requirements or []),
        province=job.province,
        country=job.country,
        remote_type=job.remote_type or ("remote" if job.is_remote else "onsite"),
        seniority=job.seniority,
        experience_min=job.experience_min,
        experience_max=job.experience_max,
        salary_min=job.salary_min,
        salary_max=job.salary_max,
        source=job.source,
        apply_url=job.apply_url or job.url,
    )


async def score_inbox_job(
    session: AsyncSession,
    inbox_job: InboxJob,
    user: User,
    *,
    prefs: UserScoringPrefs | None = None,
    candidate: CandidateProfile | None = None,
) -> JobFitScore:
    if prefs is None:
        prefs = await session.get(UserScoringPrefs, user.id)
    if candidate is None:
        candidate = await build_candidate_profile(session, user, prefs)
    result = score_job(
        _job_facts(inbox_job.job),
        candidate,
        threshold_overrides=prefs.threshold_overrides if prefs else None,
    )
    existing = await session.execute(
        select(JobFitScore).where(JobFitScore.user_id == user.id, JobFitScore.job_id == inbox_job.job_id)
    )
    fit_score = existing.scalar_one_or_none()
    if not fit_score:
        fit_score = JobFitScore(user_id=user.id, job_id=inbox_job.job_id)
        session.add(fit_score)
    fit_score.score = result.score
    fit_score.label = result.label
    fit_score.signals = result.signals
    fit_score.matched_skills = list(result.matched_skills)
    fit_score.missing_skills = list(result.missing_skills)
    fit_score.risk_flags = list(result.risk_flags)
    fit_score.recommended_action = result.recommended_action
    fit_score.explanation = result.explanation
    fit_score.recommended_category = result.recommended_category
    fit_score.category_confidence = result.category_confidence
    fit_score.updated_at = datetime.now(timezone.utc)
    await session.flush()
    inbox_job.fit_score_id = fit_score.id
    inbox_job.ai_recommended_category = result.recommended_category
    if inbox_job.status == "new" and result.score >= 60:
        inbox_job.status = "ai_reviewed"
    await session.flush()
    return fit_score


async def rescore_user_inbox(
    session: AsyncSession,
    user: User,
    *,
    prefs: UserScoringPrefs | None = None,
) -> int:
    candidate = await build_candidate_profile(session, user, prefs)
    result = await session.execute(
        select(InboxJob)
        .where(InboxJob.user_id == user.id, InboxJob.status.notin_(("archived", "duplicate")))
        .join(InboxJob.job)
        .options(selectinload(InboxJob.job))
    )
    items = result.scalars().all()
    for item in items:
        await score_inbox_job(session, item, user, prefs=prefs, candidate=candidate)
    return len(items)
