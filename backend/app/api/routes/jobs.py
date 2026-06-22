from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import ImportUrlRequest, JobListResponse, JobResponse
from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.job import Job
from app.models.user import User
from app.jobs.pipeline.ingest import ingest_job
from app.jobs.pipeline.normalizer import normalize_raw_job
from app.scrapers.url_importer import import_from_url
from app.services.job_filters import apply_canada_filter
from app.scrapers.base import RawJob

router = APIRouter()


@router.get("", response_model=JobListResponse)
async def list_jobs(
    q: str | None = None,
    company: str | None = None,
    source: str | None = None,
    remote: bool | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    query = apply_canada_filter(select(Job).where(Job.is_active == True))  # noqa: E712
    count_query = apply_canada_filter(select(func.count(Job.id)).where(Job.is_active == True))  # noqa: E712

    if q:
        pattern = f"%{q}%"
        filt = or_(Job.title.ilike(pattern), Job.company.ilike(pattern), Job.description.ilike(pattern))
        query = query.where(filt)
        count_query = count_query.where(filt)
    if company:
        query = query.where(Job.company.ilike(f"%{company}%"))
        count_query = count_query.where(Job.company.ilike(f"%{company}%"))
    if source:
        query = query.where(Job.source == source)
        count_query = count_query.where(Job.source == source)
    if remote is not None:
        query = query.where(Job.is_remote == remote)
        count_query = count_query.where(Job.is_remote == remote)

    total = (await db.execute(count_query)).scalar() or 0
    offset = (page - 1) * limit
    result = await db.execute(query.order_by(Job.first_seen.desc()).offset(offset).limit(limit))
    jobs = result.scalars().all()

    return JobListResponse(
        jobs=[JobResponse.model_validate(j) for j in jobs],
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/search", response_model=JobListResponse)
async def search_jobs(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    return await list_jobs(q=q, page=page, limit=limit, db=db)


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse.model_validate(job)


@router.post("/import-url", response_model=JobResponse)
async def import_job_url(
    body: ImportUrlRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        raw = await import_from_url(str(body.url))
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Could not load URL: {e}")

    normalized = normalize_raw_job(raw, "url_import")
    result = await ingest_job(db, normalized, user_id=user.id, captured_via="url")
    await db.commit()
    await db.refresh(result.job)
    return JobResponse.model_validate(result.job)
