from fastapi import APIRouter, Depends, HTTPException

from app.api.schemas import ScraperTriggerResponse
from app.core.auth import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.services.scraper_runner import (
    can_trigger_manual,
    get_scraper_status,
    get_source_stats,
    mark_manual_triggered,
    run_all_scrapers,
)
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.post("/trigger", response_model=ScraperTriggerResponse)
async def trigger_scraper(user: User = Depends(get_current_user)):
    if not can_trigger_manual(settings.scraper_debounce_minutes):
        raise HTTPException(
            status_code=429,
            detail=f"Please wait {settings.scraper_debounce_minutes} minutes between manual scrapes",
        )
    mark_manual_triggered()
    new_jobs = await run_all_scrapers()
    return ScraperTriggerResponse(
        new_jobs=new_jobs,
        message=f"Scrape complete. {new_jobs} new Canada-eligible jobs added.",
    )


@router.get("/sources")
async def list_sources(db: AsyncSession = Depends(get_db)):
    stats = await get_source_stats(db)
    status = get_scraper_status()
    return {"sources": stats, "last_run": status.get("last_run")}


@router.get("/status")
async def scraper_status(user: User = Depends(get_current_user)):
    return get_scraper_status()
