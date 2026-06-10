from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import MatchScoreResponse, ProfileUpdate, StructuredProfileResponse, StructuredProfileUpdate, UserResponse
from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.job import Job
from app.models.profile_structured import UserProfileStructured
from app.models.user import User
from app.schemas.resume_content import ResumeContent, empty_resume_content, resume_to_text
from app.services.job_filters import apply_canada_filter
from app.services.llm.client import get_user_llm_config
from app.services.match_scorer import extract_skills, tfidf_score
from app.services.rag.ingest import ingest_resume_content
from app.services.resume.pdf_compiler import extract_pdf_text
from app.services.resume.renderer import parse_pdf_text

router = APIRouter()


@router.get("", response_model=UserResponse)
async def get_profile(user: User = Depends(get_current_user)):
    return UserResponse.model_validate(user)


@router.put("", response_model=UserResponse)
async def update_profile(
    body: ProfileUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.resume_text is not None:
        user.resume_text = body.resume_text
        user.skills_keywords = body.skills_keywords or extract_skills(body.resume_text)
    elif body.skills_keywords is not None:
        user.skills_keywords = body.skills_keywords

    await db.commit()
    await db.refresh(user)
    return UserResponse.model_validate(user)


@router.get("/structured", response_model=StructuredProfileResponse)
async def get_structured_profile(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserProfileStructured).where(UserProfileStructured.user_id == user.id))
    row = result.scalar_one_or_none()
    if not row:
        return StructuredProfileResponse(content=empty_resume_content().model_dump())
    return StructuredProfileResponse(content=row.content_json, updated_at=row.updated_at)


@router.put("/structured", response_model=StructuredProfileResponse)
async def update_structured_profile(
    body: StructuredProfileUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    content = ResumeContent.model_validate(body.content)
    result = await db.execute(select(UserProfileStructured).where(UserProfileStructured.user_id == user.id))
    row = result.scalar_one_or_none()
    if row:
        row.content_json = content.model_dump()
    else:
        row = UserProfileStructured(user_id=user.id, content_json=content.model_dump())
        db.add(row)

    user.resume_text = resume_to_text(content)
    user.skills_keywords = extract_skills(user.resume_text)

    llm_config = await get_user_llm_config(db, user.id)
    if llm_config:
        await ingest_resume_content(db, user.id, content.model_dump(), llm_config)

    await db.commit()
    await db.refresh(row)
    return StructuredProfileResponse(content=row.content_json, updated_at=row.updated_at)


@router.post("/upload-resume")
async def upload_resume_pdf(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    raw = await file.read()
    text = extract_pdf_text(raw)
    content = parse_pdf_text(text)
    return {"content": content, "warnings": ["PDF parsing is best-effort. Review sections in the editor."] if text else ["Could not extract text from PDF"]}


@router.get("/match-scores", response_model=list[MatchScoreResponse])
async def get_match_scores(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not user.resume_text:
        return []

    result = await db.execute(apply_canada_filter(select(Job).where(Job.is_active == True)).limit(200))  # noqa: E712
    jobs = result.scalars().all()

    scores = []
    for job in jobs:
        match = tfidf_score(user.resume_text, job.description or job.title)
        scores.append(
            MatchScoreResponse(
                job_id=job.id,
                score=match["score"],
                matched_keywords=match["matched_keywords"],
            )
        )
    return sorted(scores, key=lambda s: s.score, reverse=True)
