from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


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
    job_title: str | None = None
    company_name: str | None = None
    job_url: str | None = None
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
    company_name: str | None = None
    content_json: dict | None = None
    latex_source: str | None = None
    application_id: UUID | None = None


class ResumeResponse(BaseModel):
    id: UUID
    title: str
    job_title: str | None = None
    job_url: str | None = None
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


class ResumeStatusResponse(BaseModel):
    id: UUID
    status: str
    last_step: str | None = None
    pipeline_error: str | None = None
    cover_letter_id: UUID | None = None
    ats_score: ATSScoreResponse | None = None
    updated_at: datetime
