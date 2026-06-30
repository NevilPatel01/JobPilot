from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


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
