from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.graph import run_generation_pipeline
from app.api.schemas import ATSScoreResponse, ChatRequest, ResumeCreate, ResumeResponse
from app.api.routes.resumes import _get_resume, _resume_response
from app.core.api_auth import get_user_from_api_token
from app.core.database import get_db
from app.models.cover_letter import CoverLetterDocument
from app.models.resume import ResumeDocument
from app.models.user import User
from app.schemas.resume_content import empty_resume_content
from app.services.resume.renderer import render_resume_latex

router = APIRouter()


@router.post("/resumes", response_model=ResumeResponse)
async def api_create_resume(
    body: ResumeCreate,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_user_from_api_token),
    db: AsyncSession = Depends(get_db),
):
    from app.api.routes.resumes import _get_structured_profile

    if body.source_type == "profile":
        content = await _get_structured_profile(db, user)
    else:
        content = body.content_json or empty_resume_content().model_dump()

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
    )
    db.add(resume)
    await db.commit()
    await db.refresh(resume)

    async def _run():
        from app.core.database import async_session

        async with async_session() as session:
            result = await session.execute(select(ResumeDocument).where(ResumeDocument.id == resume.id))
            doc = result.scalar_one()
            await run_generation_pipeline(session, doc)

    background_tasks.add_task(_run)
    return _resume_response(resume)


@router.get("/resumes/{resume_id}", response_model=ResumeResponse)
async def api_get_resume(
    resume_id: UUID,
    user: User = Depends(get_user_from_api_token),
    db: AsyncSession = Depends(get_db),
):
    resume = await _get_resume(db, resume_id, user.id)
    cl_result = await db.execute(select(CoverLetterDocument).where(CoverLetterDocument.resume_id == resume.id))
    cl = cl_result.scalar_one_or_none()
    return _resume_response(resume, cl.id if cl else None)


@router.post("/resumes/{resume_id}/chat")
async def api_chat(
    resume_id: UUID,
    body: ChatRequest,
    user: User = Depends(get_user_from_api_token),
    db: AsyncSession = Depends(get_db),
):
    from app.api.routes.resumes import chat_edit

    return await chat_edit(resume_id, body, user, db)


@router.get("/resumes/{resume_id}/pdf")
async def api_pdf(
    resume_id: UUID,
    user: User = Depends(get_user_from_api_token),
    db: AsyncSession = Depends(get_db),
):
    from app.api.routes.resumes import export_pdf

    return await export_pdf(resume_id, user, db)


@router.post("/resumes/{resume_id}/ats-score", response_model=ATSScoreResponse)
async def api_ats(
    resume_id: UUID,
    user: User = Depends(get_user_from_api_token),
    db: AsyncSession = Depends(get_db),
):
    from app.api.routes.resumes import run_ats_score

    return await run_ats_score(resume_id, user, db)
