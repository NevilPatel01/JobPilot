from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, HttpUrl


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
