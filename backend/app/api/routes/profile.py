from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import MatchScoreResponse, ProfileUpdate, UserResponse
from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.job import Job
from app.models.user import User
from app.services.match_scorer import extract_skills, tfidf_score

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


@router.get("/match-scores", response_model=list[MatchScoreResponse])
async def get_match_scores(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not user.resume_text:
        return []

    result = await db.execute(select(Job).where(Job.is_active == True).limit(200))  # noqa: E712
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
