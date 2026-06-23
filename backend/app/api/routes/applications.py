from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationUpdate,
    QuickSaveRequest,
)
from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.application import UserApplication
from app.models.job import Job
from app.models.job_intelligence import InboxJob
from app.models.user import User

router = APIRouter()


@router.get("", response_model=list[ApplicationResponse])
async def list_applications(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserApplication)
        .where(UserApplication.user_id == user.id)
        .order_by(UserApplication.kanban_order, UserApplication.created_at.desc())
    )
    return [ApplicationResponse.model_validate(a) for a in result.scalars().all()]


@router.post("", response_model=ApplicationResponse)
async def create_application(
    body: ApplicationCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    app = UserApplication(
        user_id=user.id,
        job_id=body.job_id,
        status=body.status,
        job_title=body.job_title,
        company=body.company,
        job_url=body.job_url,
        salary_range=body.salary_range,
        notes=body.notes,
        date_applied=body.date_applied,
    )
    db.add(app)
    await db.commit()
    await db.refresh(app)
    return ApplicationResponse.model_validate(app)


@router.patch("/{app_id}", response_model=ApplicationResponse)
async def update_application(
    app_id: UUID,
    body: ApplicationUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserApplication).where(UserApplication.id == app_id, UserApplication.user_id == user.id)
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(app, field, value)

    await db.commit()
    await db.refresh(app)
    return ApplicationResponse.model_validate(app)


@router.delete("/{app_id}")
async def delete_application(
    app_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserApplication).where(UserApplication.id == app_id, UserApplication.user_id == user.id)
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    await db.delete(app)
    await db.commit()
    return {"ok": True}


@router.post("/quick-save", response_model=ApplicationResponse)
async def quick_save(
    body: QuickSaveRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Job).where(Job.id == body.job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    existing_result = await db.execute(
        select(UserApplication).where(
            UserApplication.user_id == user.id,
            UserApplication.job_id == body.job_id,
        )
    )
    existing = existing_result.scalar_one_or_none()
    inbox_result = await db.execute(
        select(InboxJob).where(InboxJob.user_id == user.id, InboxJob.job_id == job.id)
    )
    inbox = inbox_result.scalar_one_or_none()
    if existing:
        if inbox and inbox.application_id != existing.id:
            inbox.application_id = existing.id
            inbox.tracker_summary = "To apply" if existing.status == "to_apply" else existing.status.replace("_", " ").title()
            await db.commit()
        return ApplicationResponse.model_validate(existing)

    salary = None
    if job.salary_min or job.salary_max:
        salary = f"${job.salary_min or '?'}-${job.salary_max or '?'}"

    app = UserApplication(
        user_id=user.id,
        job_id=job.id,
        status="to_apply",
        job_title=job.title,
        company=job.company,
        job_url=job.apply_url or job.url,
        salary_range=salary,
    )
    db.add(app)
    await db.flush()
    if inbox:
        inbox.application_id = app.id
        inbox.tracker_summary = "To apply"
    await db.commit()
    await db.refresh(app)
    return ApplicationResponse.model_validate(app)
