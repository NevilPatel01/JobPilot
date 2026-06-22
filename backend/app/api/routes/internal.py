from fastapi import APIRouter, Header, HTTPException, Query

from app.api.schemas import ScraperTriggerResponse
from app.core.config import settings
from app.jobs.sources.registry import SOURCE_DEFINITIONS
from app.services.scraper_runner import run_all_scrapers

router = APIRouter()


@router.post("/cron/scrape", response_model=ScraperTriggerResponse)
async def cron_scrape(
    authorization: str | None = Header(default=None),
    source: str | None = Query(default=None),
    dry_run: bool | None = Query(default=None),
):
    """Trigger scrapers from GitHub Actions or an external cron. Requires CRON_SECRET."""
    if not settings.cron_secret:
        raise HTTPException(status_code=404, detail="Cron endpoint is not configured")
    if authorization != f"Bearer {settings.cron_secret}":
        raise HTTPException(status_code=401, detail="Invalid cron authorization")
    if source and source not in SOURCE_DEFINITIONS:
        raise HTTPException(status_code=422, detail="Unknown job source")

    new_jobs = await run_all_scrapers([source] if source else None, dry_run=dry_run)
    return ScraperTriggerResponse(
        new_jobs=new_jobs,
        message=f"Cron scrape complete. {new_jobs} new Canada-eligible jobs added.",
    )
