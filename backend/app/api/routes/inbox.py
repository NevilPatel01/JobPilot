from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.schemas import (
    ImportUrlRequest,
    InboxJobResponse,
    InboxListResponse,
    InboxManualCreate,
    InboxResumeCategoryUpdate,
    InboxResumeGenerateRequest,
    InboxResumeGenerateResponse,
    InboxStatusUpdate,
    ResumeCategoryTemplateResponse,
    UserScoringPrefsResponse,
    UserScoringPrefsUpdate,
)
from app.core.auth import get_current_user
from app.core.database import async_session, get_db
from app.agents.graph import run_generation_pipeline
from app.jobs.pipeline.ingest import ingest_job
from app.jobs.inbox_actions import mark_inbox_applied
from app.jobs.pipeline.normalizer import normalize_job, normalize_raw_job
from app.jobs.resume_templates import RESUME_CATEGORIES, ensure_resume_template, seed_resume_templates
from app.jobs.scoring.service import rescore_user_inbox, score_inbox_job
from app.models.job import Job
from app.models.job_intelligence import InboxJob, JobFitScore, UserScoringPrefs
from app.models.resume import ResumeDocument
from app.models.user import User
from app.scrapers.url_importer import import_from_url
from app.services.llm.client import get_user_llm_config
from app.services.resume.renderer import render_resume_latex

router = APIRouter()


def _resume_pipeline_task(resume_id: UUID):
    async def _run():
        async with async_session() as session:
            resume = await session.get(ResumeDocument, resume_id)
            if resume:
                await run_generation_pipeline(session, resume, mode="full")

    return _run


def _response(item: InboxJob) -> InboxJobResponse:
    return InboxJobResponse.model_validate(item)


@router.get("", response_model=InboxListResponse)
async def list_inbox(
    status: str | None = None,
    province: str | None = None,
    min_score: int | None = Query(None, ge=0, le=100),
    fit_label: str | None = None,
    risk_flag: str | None = None,
    resume_category: str | None = None,
    q: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    filters = [InboxJob.user_id == user.id]
    if status:
        filters.append(InboxJob.status == status)
    if province:
        filters.append(Job.province == province.upper())
    if q:
        pattern = f"%{q}%"
        filters.append(or_(Job.title.ilike(pattern), Job.company.ilike(pattern), Job.skills.any(q)))
    if min_score is not None:
        filters.append(JobFitScore.score >= min_score)
    if fit_label:
        filters.append(JobFitScore.label == fit_label)
    if risk_flag:
        filters.append(JobFitScore.risk_flags.any(risk_flag))
    if resume_category:
        filters.append(JobFitScore.recommended_category == resume_category)

    base = (
        select(InboxJob)
        .join(InboxJob.job)
        .outerjoin(JobFitScore, InboxJob.fit_score_id == JobFitScore.id)
        .where(*filters)
    )
    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
    result = await db.execute(
        base.options(selectinload(InboxJob.job), selectinload(InboxJob.fit_score))
        .order_by(JobFitScore.score.desc().nullslast(), InboxJob.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    return InboxListResponse(
        items=[_response(item) for item in result.scalars().all()],
        total=total,
        page=page,
        limit=limit,
    )


@router.post("/manual", response_model=InboxJobResponse, status_code=201)
async def add_manual_job(
    body: InboxManualCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    normalized = normalize_job({**body.model_dump(), "source": "manual"})
    result = await ingest_job(db, normalized, user_id=user.id, captured_via="manual")
    await db.commit()
    item = await _load_inbox(db, result.inbox_job.id)
    return _response(item)


@router.post("/import-url", response_model=InboxJobResponse, status_code=201)
async def import_url_to_inbox(
    body: ImportUrlRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        raw = await import_from_url(str(body.url))
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Could not load URL: {exc}") from exc

    normalized = normalize_raw_job(raw, "url_import")
    result = await ingest_job(db, normalized, user_id=user.id, captured_via="url")
    await db.commit()
    item = await _load_inbox(db, result.inbox_job.id)
    return _response(item)


@router.post("/jobs/{job_id}", response_model=InboxJobResponse, status_code=201)
async def save_catalog_job(
    job_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    job = await db.get(Job, job_id)
    if not job or not job.is_active:
        raise HTTPException(status_code=404, detail="Job not found")
    existing = await db.execute(
        select(InboxJob).where(InboxJob.user_id == user.id, InboxJob.job_id == job_id)
    )
    item = existing.scalar_one_or_none()
    if not item:
        item = InboxJob(user_id=user.id, job_id=job_id, status="new", captured_via="catalog")
        db.add(item)
        await db.flush()
    item.job = job
    if item.status != "duplicate":
        await score_inbox_job(db, item, user)
    await db.commit()
    return _response(await _load_inbox(db, item.id))


@router.post("/rescore")
async def rescore_inbox(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    prefs = await db.get(UserScoringPrefs, user.id)
    count = await rescore_user_inbox(db, user, prefs=prefs)
    await db.commit()
    return {"scored": count}


@router.get("/resume-templates", response_model=list[ResumeCategoryTemplateResponse])
async def list_resume_templates(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        templates = await seed_resume_templates(db, user.id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    await db.commit()
    return [ResumeCategoryTemplateResponse.model_validate(template) for template in templates]


@router.post("/{inbox_id}/rescore", response_model=InboxJobResponse)
async def rescore_inbox_job(
    inbox_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = await _load_user_inbox(db, inbox_id, user.id)
    await score_inbox_job(db, item, user)
    await db.commit()
    return _response(await _load_inbox(db, item.id))


@router.patch("/{inbox_id}/resume-category", response_model=InboxJobResponse)
async def update_resume_category(
    inbox_id: UUID,
    body: InboxResumeCategoryUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = await _load_user_inbox(db, inbox_id, user.id)
    item.user_selected_category = body.category
    await db.commit()
    return _response(await _load_inbox(db, item.id))


@router.post("/{inbox_id}/generate-resume", response_model=InboxResumeGenerateResponse)
async def generate_resume_from_inbox(
    inbox_id: UUID,
    body: InboxResumeGenerateRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = await _load_user_inbox(db, inbox_id, user.id)
    if item.resume_id:
        existing = await db.get(ResumeDocument, item.resume_id)
        if existing:
            return InboxResumeGenerateResponse(
                resume_id=existing.id,
                status=existing.status,
                inbox_status=item.status,
                category=existing.resume_category or item.user_selected_category or item.ai_recommended_category or "it_support",
                existing=True,
            )
    if item.status not in {"shortlisted", "resume_ready"}:
        raise HTTPException(status_code=409, detail="Shortlist this job before generating a tailored resume")
    if not (item.job.description or "").strip():
        raise HTTPException(status_code=422, detail="Add a job description before generating a tailored resume")
    if not await get_user_llm_config(db, user.id):
        raise HTTPException(status_code=422, detail="Configure an LLM API key in Settings before generating resumes")

    category = body.category or item.user_selected_category or item.ai_recommended_category
    if category not in RESUME_CATEGORIES:
        category = "it_support"
    try:
        template = await ensure_resume_template(db, user.id, category)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    fit = item.fit_score
    why = {
        "category": category,
        "category_source": "user_override" if body.category or item.user_selected_category else "fit_recommendation",
        "category_confidence": fit.category_confidence if fit else None,
        "matched_keywords": list(fit.matched_skills) if fit else [],
        "missing_keywords": list(fit.missing_skills) if fit else [],
        "fit_score": fit.score if fit else None,
        "template_notes": template.selection_notes,
        "truthfulness": "Generated from the saved structured profile; unsupported claims are blocked by validation.",
    }
    content = template.base_content
    resume = ResumeDocument(
        user_id=user.id,
        title=f"{item.job.company} — {item.job.title}",
        status="processing",
        job_description=item.job.description,
        company_name=item.job.company,
        source_type="inbox",
        content_json=content,
        latex_source=render_resume_latex(content),
        application_id=item.application_id,
        job_id=item.job_id,
        inbox_job_id=item.id,
        resume_category=category,
        why_this_version=why,
        create_cover_letter=body.create_cover_letter,
        insights_json={"source_content": content, "why_this_version": why, "inbox_job_id": str(item.id)},
    )
    db.add(resume)
    await db.flush()
    item.resume_id = resume.id
    item.user_selected_category = body.category or item.user_selected_category
    await db.commit()
    background_tasks.add_task(_resume_pipeline_task(resume.id))
    return InboxResumeGenerateResponse(
        resume_id=resume.id,
        status=resume.status,
        inbox_status=item.status,
        category=category,
    )


@router.patch("/{inbox_id}/status", response_model=InboxJobResponse)
async def update_inbox_status(
    inbox_id: UUID,
    body: InboxStatusUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = await _load_user_inbox(db, inbox_id, user.id)
    if body.status == "applied":
        await mark_inbox_applied(db, item, user)
    else:
        item.status = body.status
    await db.commit()
    return _response(await _load_inbox(db, item.id))


@router.get("/preferences", response_model=UserScoringPrefsResponse)
async def get_scoring_preferences(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    prefs = await db.get(UserScoringPrefs, user.id)
    if not prefs:
        prefs = UserScoringPrefs(user_id=user.id)
        db.add(prefs)
        await db.commit()
        await db.refresh(prefs)
    return UserScoringPrefsResponse.model_validate(prefs)


@router.put("/preferences", response_model=UserScoringPrefsResponse)
async def update_scoring_preferences(
    body: UserScoringPrefsUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    provinces = list(dict.fromkeys(code.upper() for code in body.target_provinces))
    invalid = [code for code in provinces if code not in {"AB", "BC", "ON", "SK"}]
    if invalid:
        raise HTTPException(status_code=422, detail=f"Unsupported target provinces: {', '.join(invalid)}")
    prefs = await db.get(UserScoringPrefs, user.id)
    if not prefs:
        prefs = UserScoringPrefs(user_id=user.id)
        db.add(prefs)
    prefs.work_authorization = body.work_authorization
    prefs.target_provinces = provinces
    prefs.relocation_open = body.relocation_open
    prefs.threshold_overrides = body.threshold_overrides
    await db.flush()
    await rescore_user_inbox(db, user, prefs=prefs)
    await db.commit()
    await db.refresh(prefs)
    return UserScoringPrefsResponse.model_validate(prefs)


async def _load_inbox(db: AsyncSession, inbox_id: UUID) -> InboxJob:
    result = await db.execute(
        select(InboxJob)
        .where(InboxJob.id == inbox_id)
        .options(selectinload(InboxJob.job), selectinload(InboxJob.fit_score))
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Inbox job not found")
    return item


async def _load_user_inbox(db: AsyncSession, inbox_id: UUID, user_id: UUID) -> InboxJob:
    result = await db.execute(
        select(InboxJob)
        .where(InboxJob.id == inbox_id, InboxJob.user_id == user_id)
        .options(selectinload(InboxJob.job), selectinload(InboxJob.fit_score))
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Inbox job not found")
    return item
