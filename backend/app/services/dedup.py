from sqlalchemy.ext.asyncio import AsyncSession

from app.jobs.pipeline.ingest import ingest_job
from app.jobs.pipeline.normalizer import normalize_raw_job
from app.scrapers.base import RawJob
from app.services.location import TARGET_COUNTRY, detect_country


async def upsert_jobs(session: AsyncSession, raw_jobs: list[RawJob], source: str) -> int:
    new_count = 0
    for raw in raw_jobs:
        if not raw.url or not raw.title or not raw.company:
            continue

        country = raw.country or detect_country(raw.location, raw.description, raw.title)
        if country != TARGET_COUNTRY:
            continue

        normalized = normalize_raw_job(raw, source)
        result = await ingest_job(session, normalized)
        if result.created:
            new_count += 1

    await session.commit()
    return new_count
