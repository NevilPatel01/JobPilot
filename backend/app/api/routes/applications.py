from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy import or_, select
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
from app.models.resume import ResumeDocument
from app.models.user import User
from app.services.application_resume_storage import (
    delete_uploaded_resume,
    read_uploaded_resume,
    save_uploaded_resume,
)
from app.services.resume.latex import resolve_export_latex
from app.services.resume.pdf_compiler import compile_latex_to_pdf_with_status

router = APIRouter()


async def _resume_title(db: AsyncSession, resume_id: UUID | None) -> str | None:
    if not resume_id:
        return None
    resume = await db.get(ResumeDocument, resume_id)
    return resume.title if resume else None


async def _to_response(db: AsyncSession, app: UserApplication) -> ApplicationResponse:
    data = ApplicationResponse.model_validate(app)
    data.resume_title = await _resume_title(db, app.resume_id)
    data.has_uploaded_resume = bool(app.uploaded_resume_filename)
    return data


async def _link_resume(
    db: AsyncSession,
    user: User,
    app: UserApplication,
    resume_id: UUID | None,
) -> None:
    if resume_id is None:
        app.resume_id = None
        return
    resume = await db.get(ResumeDocument, resume_id)
    if not resume or resume.user_id != user.id:
        raise HTTPException(status_code=404, detail="Resume not found")
    app.resume_id = resume.id
    resume.application_id = app.id
    if not app.job_description and resume.job_description:
        app.job_description = resume.job_description


@router.get("", response_model=list[ApplicationResponse])
async def list_applications(
    q: str | None = Query(None, description="Search title, company, notes, or job description"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(UserApplication).where(UserApplication.user_id == user.id)
    if q and q.strip():
        pattern = f"%{q.strip()}%"
        query = query.where(
            or_(
                UserApplication.job_title.ilike(pattern),
                UserApplication.company.ilike(pattern),
                UserApplication.notes.ilike(pattern),
                UserApplication.job_description.ilike(pattern),
            )
        )
    result = await db.execute(
        query.order_by(UserApplication.kanban_order, UserApplication.created_at.desc())
    )
    apps = result.scalars().all()
    return [await _to_response(db, a) for a in apps]


@router.get("/{app_id}", response_model=ApplicationResponse)
async def get_application(
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
    return await _to_response(db, app)


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
        job_description=body.job_description,
        date_applied=body.date_applied,
    )
    db.add(app)
    await db.flush()
    if body.resume_id is not None:
        await _link_resume(db, user, app, body.resume_id)
    await db.commit()
    await db.refresh(app)
    return await _to_response(db, app)


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

    data = body.model_dump(exclude_unset=True)
    resume_id = data.pop("resume_id", ...)
    for field, value in data.items():
        setattr(app, field, value)
    if resume_id is not ...:
        await _link_resume(db, user, app, resume_id)

    await db.commit()
    await db.refresh(app)
    return await _to_response(db, app)


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
    delete_uploaded_resume(user.id, app.id)
    await db.delete(app)
    await db.commit()
    return {"ok": True}


@router.post("/{app_id}/upload-resume", response_model=ApplicationResponse)
async def upload_application_resume(
    app_id: UUID,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserApplication).where(UserApplication.id == app_id, UserApplication.user_id == user.id)
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    max_bytes = 10 * 1024 * 1024
    raw = await file.read(max_bytes + 1)
    if not raw:
        raise HTTPException(status_code=400, detail="The uploaded PDF is empty")
    if len(raw) > max_bytes:
        raise HTTPException(status_code=413, detail="Resume PDF must be 10 MB or smaller")
    save_uploaded_resume(user.id, app.id, raw)
    app.uploaded_resume_filename = file.filename[:255]
    await db.commit()
    await db.refresh(app)
    return await _to_response(db, app)


@router.delete("/{app_id}/uploaded-resume", response_model=ApplicationResponse)
async def delete_application_uploaded_resume(
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
    delete_uploaded_resume(user.id, app.id)
    app.uploaded_resume_filename = None
    await db.commit()
    await db.refresh(app)
    return await _to_response(db, app)


@router.get("/{app_id}/resume-pdf")
async def get_application_resume_pdf(
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

    uploaded = read_uploaded_resume(user.id, app.id)
    if uploaded:
        return Response(
            content=uploaded,
            media_type="application/pdf",
            headers={"Content-Disposition": f'inline; filename="{app.uploaded_resume_filename or "resume.pdf"}"'},
        )

    if app.resume_id:
        resume = await db.get(ResumeDocument, app.resume_id)
        if resume and resume.user_id == user.id:
            latex = resolve_export_latex(resume.content_json or {}, resume.latex_source)
            try:
                pdf_bytes, _ = compile_latex_to_pdf_with_status(latex)
            except RuntimeError as e:
                raise HTTPException(status_code=503, detail=str(e)) from e
            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={"Content-Disposition": 'inline; filename="resume.pdf"'},
            )

    raise HTTPException(status_code=404, detail="No resume attached to this application")


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
        if not existing.job_description and job.description:
            existing.job_description = job.description
        if inbox and inbox.application_id != existing.id:
            inbox.application_id = existing.id
            inbox.tracker_summary = "To apply" if existing.status == "to_apply" else existing.status.replace("_", " ").title()
        await db.commit()
        await db.refresh(existing)
        return await _to_response(db, existing)

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
        job_description=job.description,
    )
    db.add(app)
    await db.flush()
    if inbox:
        inbox.application_id = app.id
        inbox.tracker_summary = "To apply"
        if inbox.resume_id:
            await _link_resume(db, user, app, inbox.resume_id)
    await db.commit()
    await db.refresh(app)
    return await _to_response(db, app)
