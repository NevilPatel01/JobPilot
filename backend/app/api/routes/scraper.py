from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select

from app.api.schemas import JobSourceUpdate, ScraperRunResponse, ScraperTriggerResponse
from app.core.auth import get_current_user, require_moderator
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.models.job_intelligence import ScraperRun
from app.jobs.sources.registry import SOURCE_DEFINITIONS, ensure_source_configs
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
async def trigger_scraper(
    source: str | None = None,
    dry_run: bool | None = None,
    user: User = Depends(require_moderator),
):
    if not can_trigger_manual(settings.scraper_debounce_minutes):
        raise HTTPException(
            status_code=429,
            detail=f"Please wait {settings.scraper_debounce_minutes} minutes between manual scrapes",
        )
    mark_manual_triggered()
    if source and source not in SOURCE_DEFINITIONS:
        raise HTTPException(status_code=422, detail="Unknown job source")
    new_jobs = await run_all_scrapers([source] if source else None, dry_run=dry_run)
    return ScraperTriggerResponse(
        new_jobs=new_jobs,
        message=f"Scrape complete. {new_jobs} new Canada-eligible jobs added.",
    )


@router.get("/sources")
async def list_sources(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stats = await get_source_stats(db)
    status = get_scraper_status()
    return {"sources": stats, "last_run": status.get("last_run")}


@router.patch("/sources/{source_name}")
async def update_source(
    source_name: str,
    body: JobSourceUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if source_name not in SOURCE_DEFINITIONS:
        raise HTTPException(status_code=404, detail="Job source not found")
    configs = await ensure_source_configs(db)
    config = configs[source_name]
    config.enabled = body.enabled
    await db.commit()
    return {"source": source_name, "enabled": config.enabled}


@router.get("/runs", response_model=list[ScraperRunResponse])
async def list_scraper_runs(
    source: str | None = None,
    status: str | None = None,
    limit: int = Query(100, ge=1, le=500),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(ScraperRun)
    if source:
        query = query.where(ScraperRun.source == source)
    if status:
        query = query.where(ScraperRun.status == status)
    result = await db.execute(query.order_by(ScraperRun.started_at.desc()).limit(limit))
    return [ScraperRunResponse.model_validate(run) for run in result.scalars().all()]


@router.get("/status")
async def scraper_status(user: User = Depends(get_current_user)):
    return get_scraper_status()
