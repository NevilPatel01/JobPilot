from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl

from app.api.schemas.jobs import JobResponse
from app.api.schemas.scoring import JobFitScoreResponse

RESUME_CATEGORY_PATTERN = "^(it_support|cloud_junior_devops|fullstack_web|app_support_analyst|automation_scada)$"


class InboxManualCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    company: str = Field(min_length=1, max_length=255)
    apply_url: HttpUrl
    description: str = ""
    location: str | None = None
    province: str | None = Field(default=None, max_length=2)
    city: str | None = None
    remote_type: str | None = Field(default=None, pattern="^(remote|hybrid|onsite|unknown)$")
    job_type: str | None = None
    salary_min: int | None = Field(default=None, ge=0)
    salary_max: int | None = Field(default=None, ge=0)
    currency: str = "CAD"
    requirements: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    seniority: str | None = None
    experience_min: int | None = Field(default=None, ge=0)
    experience_max: int | None = Field(default=None, ge=0)
    posted_date: date | None = None
    closing_date: date | None = None


class InboxStatusUpdate(BaseModel):
    status: str = Field(
        pattern="^(new|ai_reviewed|shortlisted|resume_ready|applied|archived|duplicate)$"
    )


class InboxResumeCategoryUpdate(BaseModel):
    category: str | None = Field(default=None, pattern=RESUME_CATEGORY_PATTERN)


class InboxResumeGenerateRequest(BaseModel):
    category: str | None = Field(default=None, pattern=RESUME_CATEGORY_PATTERN)
    create_cover_letter: bool = False


class InboxResumeGenerateResponse(BaseModel):
    resume_id: UUID
    status: str
    inbox_status: str
    category: str
    existing: bool = False


class ResumeCategoryTemplateResponse(BaseModel):
    id: UUID
    category: str
    base_content: dict
    selection_notes: dict
    generated_from_profile_at: datetime | None
    updated_at: datetime

    model_config = {"from_attributes": True}


class InboxJobResponse(BaseModel):
    id: UUID
    user_id: UUID
    status: str
    captured_via: str
    ai_recommended_category: str | None
    user_selected_category: str | None
    tracker_summary: str | None
    application_id: UUID | None
    fit_score_id: UUID | None
    resume_id: UUID | None
    duplicate_of_id: UUID | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
    job: JobResponse
    fit_score: JobFitScoreResponse | None

    model_config = {"from_attributes": True}


class InboxListResponse(BaseModel):
    items: list[InboxJobResponse]
    total: int
    page: int
    limit: int
