from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.models.candidate import SENSITIVE_ANSWER_CATEGORIES

FactType = Literal[
    "personal", "contact", "work_authorization", "location", "target_role",
    "target_industry", "employment", "education", "certification",
    "project", "skill", "achievement", "metric",
]
FactSource = Literal["user_entered", "resume_upload", "linkedin_import", "inferred"]
VerificationStatus = Literal["unverified", "user_confirmed", "contradicted"]
AnswerCategory = Literal[
    "behavioral", "logistics", "salary", "work_authorization",
    "demographic", "legal_declaration", "other",
]


class CandidateFactCreate(BaseModel):
    fact_type: FactType
    payload: dict = Field(..., max_length=50)
    source: FactSource = "user_entered"
    is_prohibited: bool = False


class CandidateFactUpdate(BaseModel):
    payload: dict | None = Field(None, max_length=50)
    is_prohibited: bool | None = None


class SupersedeFactRequest(BaseModel):
    payload: dict = Field(..., max_length=50)


class CandidateFactResponse(BaseModel):
    id: UUID
    user_id: UUID
    fact_type: str
    payload: dict
    source: str
    verification_status: str
    confidence: float
    superseded_by_id: UUID | None
    is_prohibited: bool
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class AchievementCreate(BaseModel):
    related_fact_id: UUID | None = None
    situation: str = Field("", max_length=2000)
    task: str = Field("", max_length=2000)
    action: str = Field("", max_length=2000)
    result: str = Field("", max_length=2000)
    metrics: dict = Field(default_factory=dict, max_length=50)
    tags: list[str] = Field(default_factory=list, max_length=20)


class AchievementUpdate(BaseModel):
    related_fact_id: UUID | None = None
    situation: str | None = Field(None, max_length=2000)
    task: str | None = Field(None, max_length=2000)
    action: str | None = Field(None, max_length=2000)
    result: str | None = Field(None, max_length=2000)
    metrics: dict | None = Field(None, max_length=50)
    tags: list[str] | None = Field(None, max_length=20)


class AchievementResponse(BaseModel):
    id: UUID
    user_id: UUID
    related_fact_id: UUID | None
    situation: str
    task: str
    action: str
    result: str
    metrics: dict
    tags: list[str]
    verification_status: str
    confidence: float
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class CareerProfileCreate(BaseModel):
    name: str = Field(..., max_length=100)
    description: str = Field("", max_length=2000)
    emphasis_fact_ids: list[UUID] = Field(default_factory=list)
    positioning_statement: str = Field("", max_length=1000)
    is_default: bool = False


class CareerProfileUpdate(BaseModel):
    name: str | None = Field(None, max_length=100)
    description: str | None = Field(None, max_length=2000)
    emphasis_fact_ids: list[UUID] | None = None
    positioning_statement: str | None = Field(None, max_length=1000)


class CareerProfileResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    description: str
    emphasis_fact_ids: list[UUID]
    positioning_statement: str
    is_default: bool
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class AnswerBankEntryCreate(BaseModel):
    question_text: str = Field(..., max_length=1000)
    question_category: AnswerCategory
    answer_text: str = Field("", max_length=5000)
    related_fact_ids: list[UUID] = Field(default_factory=list)

    @model_validator(mode="after")
    def _compute_sensitivity(self) -> "AnswerBankEntryCreate":
        # is_sensitive is derived server-side from question_category, never client-set —
        # see plan Task 6 rationale (prevents a client marking a sensitive category as safe).
        return self

    @property
    def is_sensitive(self) -> bool:
        return self.question_category in SENSITIVE_ANSWER_CATEGORIES


class AnswerBankEntryUpdate(BaseModel):
    question_text: str | None = Field(None, max_length=1000)
    question_category: AnswerCategory | None = None
    answer_text: str | None = Field(None, max_length=5000)
    related_fact_ids: list[UUID] | None = None
    # no is_sensitive field on purpose: sensitivity is always derived server-side from category


class AnswerBankEntryResponse(BaseModel):
    id: UUID
    user_id: UUID
    question_text: str
    question_category: str
    answer_text: str
    is_sensitive: bool
    related_fact_ids: list[UUID]
    last_used_at: datetime | None
    usage_count: int
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}
