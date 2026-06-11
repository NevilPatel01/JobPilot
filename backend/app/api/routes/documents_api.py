from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.pipeline_status import mark_stale_processing_resumes
from app.api.schemas import ATSScoreResponse, ChatRequest, ResumeCreate, ResumeResponse
from app.api.routes.resumes import (
    _get_resume,
    _get_structured_profile,
    _pipeline_task,
    _require_llm_config,
    _resume_response,
    _resume_response_with_status,
)
from app.core.api_auth import get_user_from_api_token
from app.core.config import settings
from app.core.database import get_db
from app.core.rate_limit import limiter
from app.models.cover_letter import CoverLetterDocument
from app.models.resume import ResumeDocument
from app.models.user import User
from app.schemas.resume_content import empty_resume_content
from app.services.resume.renderer import render_resume_latex
from app.services.webhook import store_webhook_url

router = APIRouter()


@router.post("/resumes", response_model=ResumeResponse)
@limiter.limit(settings.public_api_rate_limit_create)
async def api_create_resume(
    request: Request,
    body: ResumeCreate,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_user_from_api_token),
    db: AsyncSession = Depends(get_db),
):
    await _require_llm_config(db, user.id)

    if body.source_type == "profile":
        content = await _get_structured_profile(db, user)
    else:
        content = body.content_json or empty_resume_content().model_dump()

    insights = store_webhook_url({"source_content": content}, body.webhook_url)

    resume = ResumeDocument(
        user_id=user.id,
        title=body.title,
        status="processing",
        job_description=body.job_description,
        company_url=body.company_url,
        source_type=body.source_type,
        content_json=content,
        latex_source=render_resume_latex(content),
        create_cover_letter=body.create_cover_letter,
        cover_letter_meta=body.cover_letter_meta.model_dump() if body.cover_letter_meta else None,
        insights_json=insights,
    )
    db.add(resume)
    await db.commit()
    await db.refresh(resume)

    background_tasks.add_task(_pipeline_task(resume.id, "full"))
    return _resume_response(resume)


@router.get("/resumes/{resume_id}", response_model=ResumeResponse)
@limiter.limit(settings.public_api_rate_limit_default)
async def api_get_resume(
    request: Request,
    resume_id: UUID,
    user: User = Depends(get_user_from_api_token),
    db: AsyncSession = Depends(get_db),
):
    await mark_stale_processing_resumes(db)
    resume = await _get_resume(db, resume_id, user.id)
    cl_result = await db.execute(select(CoverLetterDocument).where(CoverLetterDocument.resume_id == resume.id))
    cl = cl_result.scalar_one_or_none()
    return await _resume_response_with_status(db, resume, cl.id if cl else None)


@router.post("/resumes/{resume_id}/chat")
@limiter.limit(settings.public_api_rate_limit_default)
async def api_chat(
    request: Request,
    resume_id: UUID,
    body: ChatRequest,
    user: User = Depends(get_user_from_api_token),
    db: AsyncSession = Depends(get_db),
):
    from app.api.routes.resumes import chat_edit

    return await chat_edit(resume_id, body, user, db)


@router.get("/resumes/{resume_id}/pdf")
@limiter.limit(settings.public_api_rate_limit_default)
async def api_pdf(
    request: Request,
    resume_id: UUID,
    user: User = Depends(get_user_from_api_token),
    db: AsyncSession = Depends(get_db),
):
    from app.api.routes.resumes import export_pdf

    return await export_pdf(resume_id, user, db)


@router.post("/resumes/{resume_id}/ats-score", response_model=ATSScoreResponse)
@limiter.limit(settings.public_api_rate_limit_default)
async def api_ats(
    request: Request,
    resume_id: UUID,
    user: User = Depends(get_user_from_api_token),
    db: AsyncSession = Depends(get_db),
):
    from app.api.routes.resumes import run_ats_score

    return await run_ats_score(resume_id, user, db)
