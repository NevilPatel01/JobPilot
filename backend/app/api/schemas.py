from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl, model_validator


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
    province: str | None = None
    city: str | None = None
    remote_type: str | None = None
    job_type: str | None = None
    requirements: list[str] | None = None
    skills: list[str] | None = None
    seniority: str | None = None
    experience_min: int | None = None
    experience_max: int | None = None
    apply_url: str | None = None
    posted_date: date | None = None
    closing_date: date | None = None

    model_config = {"from_attributes": True}


class JobListResponse(BaseModel):
    jobs: list[JobResponse]
    total: int
    page: int
    limit: int


class ImportUrlRequest(BaseModel):
    url: HttpUrl


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


RESUME_CATEGORY_PATTERN = "^(it_support|cloud_junior_devops|fullstack_web|app_support_analyst|automation_scada)$"


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


class JobFitScoreResponse(BaseModel):
    id: UUID
    score: int
    label: str
    signals: dict
    matched_skills: list[str]
    missing_skills: list[str]
    risk_flags: list[str]
    recommended_action: str
    explanation: str
    recommended_category: str | None
    category_confidence: int | None
    scored_at: datetime
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


class ExtensionCaptureRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    company: str = Field(min_length=1, max_length=255)
    url: HttpUrl
    location: str | None = Field(default=None, max_length=255)
    description: str = Field(default="", max_length=100_000)
    selected_text: str = Field(default="", max_length=50_000)
    skills: list[str] = Field(default_factory=list, max_length=100)
    job_type: str | None = Field(default=None, max_length=50)
    salary_min: int | None = Field(default=None, ge=0)
    salary_max: int | None = Field(default=None, ge=0)
    currency: str = Field(default="CAD", min_length=3, max_length=8)
    source_site: str | None = Field(default=None, max_length=50)
    action: str = Field(default="inbox", pattern="^(inbox|applied)$")


class ExtensionInboxActionRequest(BaseModel):
    action: str = Field(pattern="^(shortlisted|applied|archived)$")


class ExtensionCaptureResponse(BaseModel):
    capture_id: UUID
    job_id: UUID
    inbox_job_id: UUID
    status: str
    duplicate: bool
    fit_score: int | None = None
    fit_label: str | None = None
    recommended_category: str | None = None
    application_id: UUID | None = None
    message: str


class UserScoringPrefsUpdate(BaseModel):
    work_authorization: str = Field(default="work_permit", max_length=50)
    target_provinces: list[str] = Field(default_factory=lambda: ["AB", "BC", "ON", "SK"])
    relocation_open: bool = True
    threshold_overrides: dict[str, int] | None = None

    @model_validator(mode="after")
    def validate_thresholds(self):
        if self.threshold_overrides is None:
            return self
        allowed = {"low_max", "stretch_max", "reviewed_max", "recommended_max"}
        unknown = set(self.threshold_overrides) - allowed
        if unknown:
            raise ValueError(f"Unsupported threshold keys: {', '.join(sorted(unknown))}")
        values = {
            "low_max": 39,
            "stretch_max": 59,
            "reviewed_max": 74,
            "recommended_max": 84,
            **self.threshold_overrides,
        }
        ordered = [values[key] for key in ("low_max", "stretch_max", "reviewed_max", "recommended_max")]
        if not (0 <= ordered[0] < ordered[1] < ordered[2] < ordered[3] < 100):
            raise ValueError("Fit thresholds must be ordered between 0 and 99")
        return self


class UserScoringPrefsResponse(UserScoringPrefsUpdate):
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


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


class JobSourceUpdate(BaseModel):
    enabled: bool


class JobSourceResponse(BaseModel):
    source: str
    display_name: str
    enabled: bool
    job_count: int
    credential_status: str
    rate_limit: str | None
    last_success: datetime | None
    last_error: str | None


class ScraperRunResponse(BaseModel):
    id: UUID
    source: str
    query: str | None
    city: str | None
    status: str
    fetched_count: int
    new_count: int
    duplicate_count: int
    errors: list
    duration_ms: int
    dry_run: bool
    started_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


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


class ApiKeyProbe(BaseModel):
    provider: str
    api_key: str
    base_url: str | None = None


class ApiKeyModelsResponse(BaseModel):
    chat_models: list[str]
    embedding_models: list[str]


class ApiKeyAutoSelectResponse(BaseModel):
    model_name: str
    embedding_model: str
    reason: str


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
    webhook_url: str | None = Field(
        default=None,
        description="Optional URL notified via POST when the generation pipeline completes or fails.",
    )


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
    job_id: UUID | None = None
    inbox_job_id: UUID | None = None
    resume_category: str | None = None
    why_this_version: dict | None = None
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
    path_label: str | None = None
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


class ChatExchangeResponse(BaseModel):
    user_message: ChatMessageResponse
    assistant_message: ChatMessageResponse


class ChangeActionRequest(BaseModel):
    change_id: UUID
    action: str = Field(pattern="^(accept|reject)$")


class BatchChangeActionRequest(BaseModel):
    change_ids: list[UUID]
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
    title: str | None = None
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
    hiring_manager_name: str | None = None
    hiring_manager_email: str | None = None
    street_address: str | None = None
    city: str | None = None
    state_province: str | None = None
    postal_code: str | None = None
    letter_date: str | None = None
    additional_context: str | None = None


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
