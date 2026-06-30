from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ApiKeyCreate(BaseModel):
    provider: str
    api_key: str
    base_url: str | None = None
    model_name: str | None = None
    embedding_model: str | None = None
    is_default: bool = False


class ApiKeyProbe(BaseModel):
    provider: str
    api_key: str
    base_url: str | None = None


class ApiKeyModelsResponse(BaseModel):
    chat_models: list[str]
    embedding_models: list[str]


class ApiKeyAutoSelectResponse(BaseModel):
    model_name: str
    embedding_model: str
    reason: str


class ApiKeyResponse(BaseModel):
    id: UUID
    provider: str
    api_key_masked: str
    base_url: str | None
    model_name: str | None
    embedding_model: str | None
    is_default: bool

    model_config = {"from_attributes": True}


class ApiTokenCreate(BaseModel):
    name: str


class ApiTokenResponse(BaseModel):
    id: UUID
    name: str
    token_prefix: str
    created_at: datetime
    last_used_at: datetime | None = None

    model_config = {"from_attributes": True}


class ApiTokenCreatedResponse(ApiTokenResponse):
    token: str
