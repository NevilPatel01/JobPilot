from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


RemoteType = Literal["remote", "hybrid", "onsite", "unknown"]


class NormalizedJob(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    company: str = Field(min_length=1, max_length=255)
    location: str | None = Field(default=None, max_length=255)
    province: str | None = Field(default=None, max_length=2)
    city: str | None = Field(default=None, max_length=120)
    remote_type: RemoteType = "unknown"
    job_type: str | None = Field(default=None, max_length=50)
    salary_min: int | None = Field(default=None, ge=0)
    salary_max: int | None = Field(default=None, ge=0)
    currency: str = Field(default="CAD", min_length=3, max_length=8)
    description: str = ""
    requirements: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    seniority: str | None = Field(default=None, max_length=50)
    experience_min: int | None = Field(default=None, ge=0, le=60)
    experience_max: int | None = Field(default=None, ge=0, le=60)
    apply_url: str = Field(min_length=1)
    source: str = Field(default="manual", min_length=1, max_length=100)
    source_job_id: str | None = Field(default=None, max_length=255)
    posted_date: date | None = None
    closing_date: date | None = None
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    canonical_url: str
    dedupe_hash: str = Field(min_length=64, max_length=64)

    @field_validator("title", "company")
    @classmethod
    def clean_required_text(cls, value: str) -> str:
        return " ".join(value.split())

    @field_validator("province")
    @classmethod
    def normalize_province(cls, value: str | None) -> str | None:
        return value.upper() if value else None

    @field_validator("skills", "requirements")
    @classmethod
    def remove_empty_duplicates(cls, values: list[str]) -> list[str]:
        seen: set[str] = set()
        cleaned: list[str] = []
        for value in values:
            item = " ".join(value.split())
            key = item.casefold()
            if item and key not in seen:
                seen.add(key)
                cleaned.append(item)
        return cleaned
