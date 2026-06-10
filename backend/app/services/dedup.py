from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job
from app.scrapers.base import RawJob, get_dedup_hash


async def upsert_jobs(session: AsyncSession, raw_jobs: list[RawJob], source: str) -> int:
    new_count = 0
    now = datetime.now(timezone.utc)

    for raw in raw_jobs:
        if not raw.url or not raw.title or not raw.company:
            continue

        dedup = get_dedup_hash(raw.title, raw.company)

        existing = await session.execute(select(Job).where(Job.dedup_hash == dedup))
        job = existing.scalar_one_or_none()

        if job:
            job.last_verified = now
            job.is_active = True
            if raw.description and len(raw.description) > len(job.description or ""):
                job.description = raw.description
            continue

        stmt = (
            insert(Job)
            .values(
                title=raw.title[:255],
                company=raw.company[:255],
                url=raw.url,
                description=raw.description,
                salary_min=raw.salary_min,
                salary_max=raw.salary_max,
                location=raw.location,
                is_remote=raw.is_remote,
                tech_stack=raw.tech_stack,
                employment_type=raw.employment_type,
                source=source,
                source_id=raw.source_id,
                dedup_hash=dedup,
                first_seen=now,
                last_verified=now,
                is_active=True,
            )
            .on_conflict_do_nothing(index_elements=["dedup_hash"])
        )
        result = await session.execute(stmt)
        if result.rowcount:
            new_count += 1

    await session.commit()
    return new_count
