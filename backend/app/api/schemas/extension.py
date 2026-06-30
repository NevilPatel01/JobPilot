from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ExtensionCaptureRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    company: str = Field(min_length=1, max_length=255)
    url: str
    location: str | None = Field(default=None, max_length=255)

    @field_validator("url")
    @classmethod
    def _validate_url(cls, value: str) -> str:
        candidate = (value or "").strip()
        if not candidate.startswith(("http://", "https://")):
            raise ValueError("url must be an absolute http(s) URL")
        return candidate
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
