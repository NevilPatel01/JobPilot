from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


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
