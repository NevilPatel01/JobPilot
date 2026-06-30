from uuid import UUID

from pydantic import BaseModel


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
