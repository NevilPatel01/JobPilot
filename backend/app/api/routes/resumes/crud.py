from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.resumes._helpers import (
    _get_resume,
    _get_structured_profile,
    _pipeline_task,
    _require_llm_config,
    _resume_response,
    _resume_response_with_status,
)
from app.api.schemas import (
    ResumeCreate,
    ResumeListResponse,
    ResumeResponse,
    ResumeStatusResponse,
    ResumeUpdate,
)
from app.agents.pipeline_status import mark_stale_processing_resumes, get_pipeline_status
from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.cover_letter import CoverLetterDocument
from app.models.resume import ATSScore, ResumeDocument
from app.models.user import User
from app.schemas.resume_content import empty_resume_content
from app.services.ats.persist import save_ats_score
from app.services.resume.renderer import render_resume_html, render_resume_latex, resolve_export_latex
from app.services.resume.pdf_compiler import compile_latex_to_pdf_with_status
from app.services.webhook import store_webhook_url
from app.api.routes.resumes._helpers import _ats_response

router = APIRouter()


@router.get("/", response_model=ResumeListResponse)
async def list_resumes(
    search: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await mark_stale_processing_resumes(db)
    q = select(ResumeDocument).where(ResumeDocument.user_id == user.id).order_by(ResumeDocument.updated_at.desc())
    if search:
        q = q.where(ResumeDocument.title.ilike(f"%{search}%"))
    result = await db.execute(q)
    resumes = result.scalars().all()

    cl_map: dict = {}
    if resumes:
        cl_result = await db.execute(
            select(CoverLetterDocument).where(
                CoverLetterDocument.user_id == user.id,
                CoverLetterDocument.resume_id.in_([r.id for r in resumes]),
            )
        )
        for cl in cl_result.scalars().all():
            if cl.resume_id:
                cl_map[cl.resume_id] = cl.id

    return ResumeListResponse(
        resumes=[
            _resume_response(
                r,
                cl_map.get(r.id),
                pipeline_error=(r.insights_json or {}).get("pipeline_error") if r.status == "failed" else None,
                last_step=(r.insights_json or {}).get("last_step"),
            )
            for r in resumes
        ],
        total=len(resumes),
    )


@router.post("/", response_model=ResumeResponse)
async def create_resume(
    body: ResumeCreate,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _require_llm_config(db, user.id)

    if body.source_type == "profile":
        content = await _get_structured_profile(db, user)
    else:
        content = body.content_json or empty_resume_content().model_dump()

    insights = {
        "source_content": content,
        "job_title": body.job_title,
        "job_url": body.job_url,
    }
    insights = {k: v for k, v in insights.items() if v}
    insights = store_webhook_url(insights, body.webhook_url)

    resume = ResumeDocument(
        user_id=user.id,
        title=body.title,
        status="processing",
        job_description=body.job_description,
        company_url=body.company_url,
        company_name=body.company_name,
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


@router.get("/{resume_id}/status", response_model=ResumeStatusResponse)
async def get_resume_status(
    resume_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await mark_stale_processing_resumes(db)
    resume = await _get_resume(db, resume_id, user.id)
    cl_result = await db.execute(select(CoverLetterDocument).where(CoverLetterDocument.resume_id == resume.id))
    cl = cl_result.scalar_one_or_none()
    ats_result = await db.execute(
        select(ATSScore).where(ATSScore.resume_id == resume.id).order_by(ATSScore.created_at.desc()).limit(1)
    )
    ats = ats_result.scalar_one_or_none()
    last_step, pipeline_error = await get_pipeline_status(db, resume.id)
    if resume.status != "failed":
        pipeline_error = None
    insights = resume.insights_json or {}
    return ResumeStatusResponse(
        id=resume.id,
        status=resume.status,
        last_step=last_step or insights.get("last_step"),
        pipeline_error=pipeline_error or insights.get("pipeline_error"),
        cover_letter_id=cl.id if cl else None,
        ats_score=_ats_response(ats) if ats else None,
        updated_at=resume.updated_at,
    )


@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(
    resume_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await mark_stale_processing_resumes(db)
    resume = await _get_resume(db, resume_id, user.id)
    cl_result = await db.execute(select(CoverLetterDocument).where(CoverLetterDocument.resume_id == resume.id))
    cl = cl_result.scalar_one_or_none()
    return await _resume_response_with_status(db, resume, cl.id if cl else None)


@router.patch("/{resume_id}", response_model=ResumeResponse)
async def update_resume(
    resume_id: UUID,
    body: ResumeUpdate,
    rescore: bool = Query(False),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    resume = await _get_resume(db, resume_id, user.id)
    if body.title is not None:
        resume.title = body.title
    if body.company_name is not None:
        resume.company_name = body.company_name
    if body.content_json is not None:
        resume.content_json = body.content_json
        # Keep the PDF in sync with the structured content. An explicit
        # latex_source in the same request still wins (intentional raw-LaTeX save).
        if body.latex_source is None:
            resume.latex_source = render_resume_latex(resume.content_json)
    if body.latex_source is not None:
        resume.latex_source = body.latex_source
    if body.application_id is not None:
        resume.application_id = body.application_id
    await db.commit()
    if rescore and body.content_json is not None:
        await save_ats_score(db, resume, user.id, enrich_llm=True)
        await db.commit()
    await db.refresh(resume)
    return _resume_response(resume)


@router.delete("/{resume_id}")
async def delete_resume(
    resume_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    resume = await _get_resume(db, resume_id, user.id)
    await db.delete(resume)
    await db.commit()
    return {"ok": True}


@router.get("/{resume_id}/preview")
async def preview_resume(
    resume_id: UUID,
    format: str = "latex",
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    resume = await _get_resume(db, resume_id, user.id)
    if format == "html":
        return Response(content=render_resume_html(resume.content_json), media_type="text/html")
    return {"latex": resolve_export_latex(resume.content_json, resume.latex_source)}


@router.get("/{resume_id}/pdf")
async def export_pdf(
    resume_id: UUID,
    inline: bool = Query(False, description="Use inline disposition for browser PDF preview"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from fastapi import HTTPException
    resume = await _get_resume(db, resume_id, user.id)
    latex = resolve_export_latex(resume.content_json, resume.latex_source)
    try:
        pdf_bytes, used_fallback = compile_latex_to_pdf_with_status(latex)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    disposition = "inline" if inline else "attachment"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'{disposition}; filename="resume.pdf"',
            # Lets the editor warn the user that Tectonic was unavailable and a
            # plain-text fallback PDF was served instead of the styled template.
            "X-PDF-Fallback": "true" if used_fallback else "false",
            "Access-Control-Expose-Headers": "X-PDF-Fallback",
        },
    )


@router.post("/{resume_id}/regenerate-latex", response_model=ResumeResponse)
async def regenerate_latex(
    resume_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    resume = await _get_resume(db, resume_id, user.id)
    resume.latex_source = render_resume_latex(resume.content_json)
    await db.commit()
    await db.refresh(resume)
    return _resume_response(resume)
