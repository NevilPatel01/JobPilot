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
    country: str | None
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


# --- Structured profile & resume ---

class StructuredProfileResponse(BaseModel):
    content: dict
    updated_at: datetime | None = None


class StructuredProfileUpdate(BaseModel):
    content: dict


class ApiKeyCreate(BaseModel):
    provider: str
    api_key: str
    base_url: str | None = None
    model_name: str | None = None
    embedding_model: str | None = None
    is_default: bool = False


class ApiKeyResponse(BaseModel):
    id: UUID
    provider: str
    api_key_masked: str
    base_url: str | None
    model_name: str | None
    embedding_model: str | None
    is_default: bool

    model_config = {"from_attributes": True}


class ApiTokenCreate(BaseModel):
    name: str


class ApiTokenResponse(BaseModel):
    id: UUID
    name: str
    token_prefix: str
    created_at: datetime
    last_used_at: datetime | None = None

    model_config = {"from_attributes": True}


class ApiTokenCreatedResponse(ApiTokenResponse):
    token: str


class CoverLetterMeta(BaseModel):
    hiring_manager_name: str | None = None
    hiring_manager_email: str | None = None
    street_address: str | None = None
    city: str | None = None
    state_province: str | None = None
    postal_code: str | None = None
    letter_date: str | None = None
    additional_context: str | None = None


class ResumeCreate(BaseModel):
    title: str
    job_description: str
    company_url: str | None = None
    source_type: str = "profile"
    content_json: dict | None = None
    create_cover_letter: bool = False
    cover_letter_meta: CoverLetterMeta | None = None


class ResumeUpdate(BaseModel):
    title: str | None = None
    content_json: dict | None = None
    latex_source: str | None = None
    application_id: UUID | None = None


class ResumeResponse(BaseModel):
    id: UUID
    title: str
    status: str
    job_description: str | None
    company_url: str | None
    company_name: str | None
    source_type: str
    content_json: dict
    latex_source: str | None
    insights_json: dict | None
    create_cover_letter: bool
    cover_letter_meta: dict | None
    application_id: UUID | None
    created_at: datetime
    updated_at: datetime
    cover_letter_id: UUID | None = None
    pipeline_error: str | None = None
    last_step: str | None = None

    model_config = {"from_attributes": True}


class ResumeListResponse(BaseModel):
    resumes: list[ResumeResponse]
    total: int


class ChatRequest(BaseModel):
    message: str


class PendingChangeResponse(BaseModel):
    id: UUID
    path: str
    old_value: str | None
    new_value: str | None
    status: str

    model_config = {"from_attributes": True}


class ChatMessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    pending_changes: list[PendingChangeResponse] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class ChangeActionRequest(BaseModel):
    change_id: UUID
    action: str = Field(pattern="^(accept|reject)$")


class ATSSuggestionItem(BaseModel):
    text: str
    prompt: str
    priority: str = "medium"
    category: str = "general"


class ATSScoreResponse(BaseModel):
    id: UUID
    overall_score: int
    keyword_match: int
    formatting_score: int
    semantic_score: int = 0
    skills_coverage: int = 0
    section_score: int = 0
    matched_keywords: list[str] | None = None
    missing_keywords: list[str] | None
    suggestions: list[str] = []
    suggestion_items: list[ATSSuggestionItem] = []
    breakdown: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ATSScoreHistoryResponse(BaseModel):
    scores: list[ATSScoreResponse]
    total: int


class CoverLetterCreate(BaseModel):
    title: str
    resume_id: UUID | None = None
    hiring_manager_name: str | None = None
    hiring_manager_email: str | None = None
    street_address: str | None = None
    city: str | None = None
    state_province: str | None = None
    postal_code: str | None = None
    letter_date: str | None = None
    additional_context: str | None = None
    content_json: dict | None = None


class CoverLetterUpdate(BaseModel):
    title: str | None = None
    content_json: dict | None = None
    latex_source: str | None = None


class CoverLetterResponse(BaseModel):
    id: UUID
    title: str
    status: str
    resume_id: UUID | None
    hiring_manager_name: str | None
    hiring_manager_email: str | None
    street_address: str | None
    city: str | None
    state_province: str | None
    postal_code: str | None
    letter_date: str | None
    additional_context: str | None
    content_json: dict
    latex_source: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CoverLetterListResponse(BaseModel):
    cover_letters: list[CoverLetterResponse]
    total: int
