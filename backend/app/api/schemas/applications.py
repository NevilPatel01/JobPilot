from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel


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
