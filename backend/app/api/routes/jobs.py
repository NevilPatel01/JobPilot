from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import ImportUrlRequest, JobListResponse, JobResponse
from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.job import Job
from app.models.user import User
from app.scrapers.url_importer import import_from_url
from app.services.dedup import upsert_jobs
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
    query = select(Job).where(Job.is_active == True)  # noqa: E712
    count_query = select(func.count(Job.id)).where(Job.is_active == True)  # noqa: E712

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
        raw = await import_from_url(body.url)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Could not load URL: {e}")

    await upsert_jobs(db, [raw], "custom")
    result = await db.execute(select(Job).where(Job.url == body.url))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=500, detail="Failed to save imported job")
    return JobResponse.model_validate(job)
