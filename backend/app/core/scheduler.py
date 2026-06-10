from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.services.scraper_runner import run_all_scrapers

scheduler = AsyncIOScheduler()


def start_scheduler() -> None:
    if scheduler.running:
        return
    scheduler.add_job(run_all_scrapers, "cron", hour=2, minute=0, id="daily_scrape")
    scheduler.start()
    print("[Scheduler] Started — daily scrape at 02:00 UTC")
