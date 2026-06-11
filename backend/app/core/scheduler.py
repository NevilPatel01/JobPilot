from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.agents.pipeline_status import mark_stale_processing_resumes
from app.core.database import async_session
from app.services.scraper_runner import run_all_scrapers

scheduler = AsyncIOScheduler()


async def _sweep_stale_resumes() -> None:
    async with async_session() as session:
        count = await mark_stale_processing_resumes(session)
        if count:
            print(f"[Scheduler] Marked {count} stale resume pipeline(s) as failed")


def start_scheduler() -> None:
    if scheduler.running:
        return
    scheduler.add_job(run_all_scrapers, "cron", hour=2, minute=0, id="daily_scrape")
    scheduler.add_job(_sweep_stale_resumes, "interval", minutes=15, id="stale_resume_sweep")
    scheduler.start()
    print("[Scheduler] Started — daily scrape at 02:00 UTC, stale resume sweep every 15m")
