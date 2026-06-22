from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.agents.pipeline_status import mark_stale_processing_resumes
from app.core.config import settings
from app.core.database import async_session
from app.services.scraper_runner import run_all_scrapers

scheduler = AsyncIOScheduler(timezone=settings.scraper_timezone)


async def _sweep_stale_resumes() -> None:
    async with async_session() as session:
        count = await mark_stale_processing_resumes(session)
        if count:
            print(f"[Scheduler] Marked {count} stale resume pipeline(s) as failed")


def start_scheduler() -> None:
    if scheduler.running:
        return
    if settings.job_intelligence_enabled:
        scheduler.add_job(
            run_all_scrapers,
            "cron",
            hour=settings.scraper_morning_hour,
            minute=0,
            id="morning_job_intelligence",
        )
        if settings.scraper_evening_enabled:
            scheduler.add_job(
                run_all_scrapers,
                "cron",
                hour=settings.scraper_evening_hour,
                minute=0,
                id="evening_job_intelligence",
            )
    scheduler.add_job(_sweep_stale_resumes, "interval", minutes=15, id="stale_resume_sweep")
    scheduler.start()
    schedule = f"{settings.scraper_morning_hour:02d}:00"
    if settings.scraper_evening_enabled:
        schedule += f" and {settings.scraper_evening_hour:02d}:00"
    print(f"[Scheduler] Started — job collection at {schedule} {settings.scraper_timezone}, stale resume sweep every 15m")
