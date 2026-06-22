from dataclasses import dataclass
from difflib import SequenceMatcher

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.jobs.pipeline.contracts import NormalizedJob
from app.models.job import Job


@dataclass(frozen=True)
class DuplicateMatch:
    job: Job
    reason: str
    fuzzy: bool = False


def description_similarity(left: str | None, right: str | None) -> float:
    if not left or not right:
        return 0.0
    return SequenceMatcher(None, left.casefold()[:6000], right.casefold()[:6000]).ratio()


async def find_duplicate(
    session: AsyncSession,
    job: NormalizedJob,
    *,
    fuzzy_threshold: float = 0.92,
) -> DuplicateMatch | None:
    exact = await session.execute(
        select(Job).where(or_(Job.canonical_url == job.canonical_url, Job.dedup_hash == job.dedupe_hash)).limit(1)
    )
    exact_job = exact.scalar_one_or_none()
    if exact_job:
        reason = "canonical_url" if exact_job.canonical_url == job.canonical_url else "identity"
        return DuplicateMatch(job=exact_job, reason=reason)

    candidates = await session.execute(
        select(Job)
        .where(Job.company.ilike(job.company), Job.title.ilike(job.title))
        .order_by(Job.first_seen.desc())
        .limit(20)
    )
    for candidate in candidates.scalars():
        if description_similarity(candidate.description, job.description) >= fuzzy_threshold:
            return DuplicateMatch(job=candidate, reason="description", fuzzy=True)
    return None
