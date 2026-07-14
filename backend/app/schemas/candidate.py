from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.models.candidate import SENSITIVE_ANSWER_CATEGORIES

FactType = Literal[
    "personal", "contact", "work_authorization", "location", "target_role",
    "target_industry", "employment", "education", "certification",
    "project", "skill", "achievement", "metric",
]
FactSource = Literal["user_entered", "resume_upload", "linkedin_import", "inferred", "github_import"]
VerificationStatus = Literal["unverified", "user_confirmed", "contradicted"]
AnswerCategory = Literal[
    "behavioral", "logistics", "salary", "work_authorization",
    "demographic", "legal_declaration", "other",
]


# --- typed fact payloads (PHASE_1_IMPLEMENTATION_SPEC §Schema changes) ---
# extra="allow": payloads may carry additional user keys beyond the typed core.


class _FactPayload(BaseModel):
    model_config = {"extra": "allow"}


class EmploymentPayload(_FactPayload):
    employer: str = Field(..., min_length=1, max_length=255)
    title: str = Field(..., min_length=1, max_length=255)
    start_date: date | None = None
    end_date: date | None = None
    location: str | None = Field(None, max_length=255)
    summary: str = Field("", max_length=2000)


class EducationPayload(_FactPayload):
    institution: str = Field(..., min_length=1, max_length=255)
    credential: str = Field("", max_length=255)
    field_of_study: str = Field("", max_length=255)
    start_date: date | None = None
    end_date: date | None = None


class CertificationPayload(_FactPayload):
    name: str = Field(..., min_length=1, max_length=255)
    issuer: str = Field("", max_length=255)
    issued_date: date | None = None
    expires_date: date | None = None


class SkillPayload(_FactPayload):
    name: str = Field(..., min_length=1, max_length=120)
    level: str | None = Field(None, max_length=40)
    years: float | None = Field(None, ge=0, le=60)


class WorkAuthorizationPayload(_FactPayload):
    status: str = Field(..., min_length=1, max_length=80)  # e.g. citizen, permanent_resident, work_permit
    country: str = Field("CA", min_length=2, max_length=2)


class ProjectPayload(_FactPayload):
    name: str = Field(..., min_length=1, max_length=255)
    url: str = Field("", max_length=500)  # provenance: repo html_url for github origin
    one_liner: str = Field("", max_length=300)
    description: str = Field("", max_length=2000)
    tech_stack: list[str] = Field(default_factory=list, max_length=30)
    highlights: list[str] = Field(default_factory=list, max_length=10)
    stars: int = Field(0, ge=0)
    last_pushed: date | None = None
    origin: Literal["github", "manual", "resume_upload"] = "manual"
    pinned: bool = False


PAYLOAD_MODELS: dict[str, type[BaseModel]] = {
    "employment": EmploymentPayload,
    "education": EducationPayload,
    "certification": CertificationPayload,
    "skill": SkillPayload,
    "work_authorization": WorkAuthorizationPayload,
    "project": ProjectPayload,
}


def validate_fact_payload(fact_type: str, payload: dict) -> dict:
    """Validate + normalize a fact payload for its type (dates → ISO strings).
    Fact types without a typed model pass through unchanged."""
    model = PAYLOAD_MODELS.get(fact_type)
    if model is None:
        return payload
    return model.model_validate(payload).model_dump(mode="json", exclude_none=True)


class CandidateFactCreate(BaseModel):
    fact_type: FactType
    payload: dict = Field(..., max_length=50)
    source: FactSource = "user_entered"
    is_prohibited: bool = False

    @model_validator(mode="after")
    def _validate_typed_payload(self) -> "CandidateFactCreate":
        self.payload = validate_fact_payload(self.fact_type, self.payload)
        return self


class CandidateFactUpdate(BaseModel):
    # payload is validated against the existing fact's type in the service layer,
    # since fact_type is not part of the update body
    payload: dict | None = Field(None, max_length=50)
    is_prohibited: bool | None = None


class SupersedeFactRequest(BaseModel):
    payload: dict = Field(..., max_length=50)


class ResumeTextImportRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=50000)


class GitHubImportRequest(BaseModel):
    username: str | None = Field(None, max_length=100)


class ConfirmImportRequest(BaseModel):
    facts: list[dict] = Field(..., max_length=200)  # items validated as CandidateFactCreate in the service


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
