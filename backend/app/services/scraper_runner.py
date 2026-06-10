from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.job import Job
from app.scrapers.hackernews import HackerNewsScraper
from app.scrapers.remoteok import RemoteOKScraper
from app.scrapers.weworkremotely import WeWorkRemotelyScraper
from app.services.dedup import upsert_jobs

SCRAPERS = [
    RemoteOKScraper(),
    WeWorkRemotelyScraper(),
    HackerNewsScraper(),
]

_scraper_status = {"status": "idle", "last_run": None, "last_new_jobs": 0, "error": None}
_last_manual_run: datetime | None = None


def get_scraper_status() -> dict:
    return _scraper_status.copy()


async def run_all_scrapers() -> int:
    global _scraper_status
    _scraper_status = {"status": "running", "last_run": None, "last_new_jobs": 0, "error": None}
    total_new = 0

    try:
        async with AsyncSessionLocal() as session:
            for scraper in SCRAPERS:
                try:
                    jobs = await scraper.fetch()
                    new_count = await upsert_jobs(session, jobs, scraper.source_name)
                    total_new += new_count
                    print(f"[Scraper] {scraper.source_name}: {len(jobs)} fetched, {new_count} new")
                except Exception as e:
                    print(f"[Scraper] {scraper.source_name} error: {e}")

        _scraper_status = {
            "status": "idle",
            "last_run": datetime.now(timezone.utc).isoformat(),
            "last_new_jobs": total_new,
            "error": None,
        }
    except Exception as e:
        _scraper_status = {
            "status": "error",
            "last_run": datetime.now(timezone.utc).isoformat(),
            "last_new_jobs": total_new,
            "error": str(e),
        }

    return total_new


def can_trigger_manual(debounce_minutes: int) -> bool:
    global _last_manual_run
    if _last_manual_run is None:
        return True
    elapsed = (datetime.now(timezone.utc) - _last_manual_run).total_seconds() / 60
    return elapsed >= debounce_minutes


def mark_manual_triggered() -> None:
    global _last_manual_run
    _last_manual_run = datetime.now(timezone.utc)


async def get_source_stats(session: AsyncSession) -> list[dict]:
    result = await session.execute(
        select(Job.source, func.count(Job.id)).where(Job.is_active == True).group_by(Job.source)  # noqa: E712
    )
    return [{"source": row[0], "job_count": row[1]} for row in result.all()]
