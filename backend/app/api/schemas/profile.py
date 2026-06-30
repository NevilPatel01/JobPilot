from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ProfileUpdate(BaseModel):
    resume_text: str | None = None
    skills_keywords: list[str] | None = None


class MatchScoreResponse(BaseModel):
    job_id: UUID
    score: float
    matched_keywords: list[str]


class ScoringStatusResponse(BaseModel):
    ready: bool


class StructuredProfileResponse(BaseModel):
    content: dict
    updated_at: datetime | None = None


class StructuredProfileUpdate(BaseModel):
    content: dict
