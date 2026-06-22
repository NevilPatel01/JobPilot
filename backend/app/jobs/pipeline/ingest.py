from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.jobs.pipeline.contracts import NormalizedJob
from app.jobs.pipeline.dedup import DuplicateMatch, find_duplicate
from app.models.job import Job
from app.models.job_intelligence import InboxJob
from app.models.user import User
from app.jobs.scoring.service import score_inbox_job


@dataclass(frozen=True)
class IngestionResult:
    job: Job
    inbox_job: InboxJob | None
    created: bool
    duplicate_reason: str | None = None


def _update_existing(job: Job, data: NormalizedJob) -> None:
    job.last_verified = datetime.now(timezone.utc)
    job.is_active = True
    if len(data.description) > len(job.description or ""):
        job.description = data.description
    for field in ("location", "province", "city", "remote_type", "job_type", "seniority", "apply_url"):
        value = getattr(data, field)
        if value:
            setattr(job, field, value)
    if data.skills:
        job.skills = data.skills
        job.tech_stack = data.skills


async def ingest_job(
    session: AsyncSession,
    data: NormalizedJob,
    *,
    user_id: UUID | None = None,
    captured_via: str = "scraper",
) -> IngestionResult:
    duplicate = await find_duplicate(session, data)
    created = duplicate is None or duplicate.fuzzy

    if created:
        job = Job(
            title=data.title,
            company=data.company,
            url=data.apply_url,
            description=data.description,
            salary_min=data.salary_min,
            salary_max=data.salary_max,
            salary_currency=data.currency,
            location=data.location,
            country="CA",
            is_remote=data.remote_type == "remote",
            tech_stack=data.skills or None,
            employment_type=data.job_type,
            province=data.province,
            city=data.city,
            remote_type=data.remote_type,
            job_type=data.job_type,
            requirements=data.requirements or None,
            skills=data.skills or None,
            seniority=data.seniority,
            experience_min=data.experience_min,
            experience_max=data.experience_max,
            apply_url=data.apply_url,
            canonical_url=data.canonical_url,
            canonical_job_id=duplicate.job.id if duplicate else None,
            posted_date=data.posted_date,
            closing_date=data.closing_date,
            raw_payload=data.raw_payload or None,
            source=data.source,
            source_id=data.source_job_id,
            dedup_hash=data.dedupe_hash,
        )
        session.add(job)
        await session.flush()
    else:
        job = duplicate.job
        _update_existing(job, data)

    inbox_job = None
    if user_id:
        existing_inbox = await session.execute(
            select(InboxJob).where(InboxJob.user_id == user_id, InboxJob.job_id == job.id)
        )
        inbox_job = existing_inbox.scalar_one_or_none()
        if not inbox_job:
            inbox_job = InboxJob(
                user_id=user_id,
                job_id=job.id,
                status="duplicate" if duplicate and duplicate.fuzzy else "new",
                captured_via=captured_via,
            )
            session.add(inbox_job)
            await session.flush()
        user = await session.get(User, user_id)
        if user and inbox_job.status != "duplicate":
            # Relationship assignment is explicit because the job may have been loaded through a dedup match.
            inbox_job.job = job
            await score_inbox_job(session, inbox_job, user)

    return IngestionResult(
        job=job,
        inbox_job=inbox_job,
        created=created,
        duplicate_reason=duplicate.reason if duplicate else None,
    )
