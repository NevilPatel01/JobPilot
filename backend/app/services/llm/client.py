from dataclasses import dataclass

import httpx
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crypto import decrypt_value
from app.models.api_key import UserApiKey


@dataclass
class LLMConfig:
    provider: str
    api_key: str
    base_url: str | None
    model_name: str
    embedding_model: str


DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_EMBEDDING = "text-embedding-3-small"


async def get_user_llm_config(db: AsyncSession, user_id) -> LLMConfig | None:
    result = await db.execute(
        select(UserApiKey)
        .where(UserApiKey.user_id == user_id)
        .order_by(UserApiKey.is_default.desc(), UserApiKey.created_at.desc())
    )
    keys = result.scalars().all()
    if not keys:
        return None
    key = next((k for k in keys if k.is_default), keys[0])
    return LLMConfig(
        provider=key.provider,
        api_key=decrypt_value(key.api_key_enc),
        base_url=key.base_url,
        model_name=key.model_name or DEFAULT_MODEL,
        embedding_model=key.embedding_model or DEFAULT_EMBEDDING,
    )


def create_chat_model(config: LLMConfig, temperature: float = 0.3) -> ChatOpenAI:
    kwargs: dict = {
        "api_key": config.api_key,
        "model": config.model_name,
        "temperature": temperature,
    }
    if config.base_url:
        kwargs["base_url"] = config.base_url
    return ChatOpenAI(**kwargs)


def create_embeddings(config: LLMConfig) -> OpenAIEmbeddings:
    kwargs: dict = {
        "api_key": config.api_key,
        "model": config.embedding_model,
    }
    if config.base_url:
        kwargs["base_url"] = config.base_url
    return OpenAIEmbeddings(**kwargs)


async def test_api_key(config: LLMConfig) -> bool:
    base = (config.base_url or "https://api.openai.com/v1").rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.get(
                f"{base}/models",
                headers={"Authorization": f"Bearer {config.api_key}"},
            )
            return res.status_code == 200
    except Exception:
        return False
