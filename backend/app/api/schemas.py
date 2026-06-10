from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    version: str


class AuthCallbackRequest(BaseModel):
    email: str
    name: str | None = None
    avatar_url: str | None = None
    oauth_provider: str
    oauth_id: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class UserResponse(BaseModel):
    id: UUID
    email: str
    name: str | None
    avatar_url: str | None
    role: str
    resume_text: str | None = None
    skills_keywords: list[str] | None = None

    model_config = {"from_attributes": True}


class JobResponse(BaseModel):
    id: UUID
    title: str
    company: str
    url: str
    description: str | None
    salary_min: int | None
    salary_max: int | None
    salary_currency: str
    location: str | None
    is_remote: bool
    tech_stack: list[str] | None
    source: str
    first_seen: datetime
    last_verified: datetime
    is_active: bool

    model_config = {"from_attributes": True}


class JobListResponse(BaseModel):
    jobs: list[JobResponse]
    total: int
    page: int
    limit: int


class ImportUrlRequest(BaseModel):
    url: str


class ApplicationCreate(BaseModel):
    status: str = "to_apply"
    job_title: str
    company: str
    job_url: str | None = None
    salary_range: str | None = None
    notes: str | None = None
    date_applied: date | None = None
    job_id: UUID | None = None


class ApplicationUpdate(BaseModel):
    status: str | None = None
    job_title: str | None = None
    company: str | None = None
    job_url: str | None = None
    salary_range: str | None = None
    notes: str | None = None
    date_applied: date | None = None
    kanban_order: int | None = None


class ApplicationResponse(BaseModel):
    id: UUID
    user_id: UUID
    job_id: UUID | None
    status: str
    job_title: str | None
    company: str | None
    job_url: str | None
    salary_range: str | None
    notes: str | None
    date_applied: date | None
    kanban_order: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class QuickSaveRequest(BaseModel):
    job_id: UUID


class ProfileUpdate(BaseModel):
    resume_text: str | None = None
    skills_keywords: list[str] | None = None


class MatchScoreResponse(BaseModel):
    job_id: UUID
    score: float
    matched_keywords: list[str]


class ScraperTriggerResponse(BaseModel):
    new_jobs: int
    message: str


class AnalyticsSummary(BaseModel):
    total_tracked: int
    total_applied: int
    interview_rate: float
    active_jobs_in_db: int
    applications_over_time: list[dict]
    status_breakdown: dict[str, int]
    top_companies: list[dict]
    source_distribution: dict[str, int]
