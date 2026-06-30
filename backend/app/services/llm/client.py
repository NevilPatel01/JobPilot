import logging
from dataclasses import dataclass

from cryptography.fernet import InvalidToken
import httpx
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crypto import decrypt_value
from app.models.api_key import UserApiKey

KEYWORD_SEARCH_EMBEDDING = "keyword-search"


@dataclass
class LLMConfig:
    provider: str
    api_key: str
    base_url: str | None
    model_name: str
    embedding_model: str


DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_EMBEDDING = "text-embedding-3-small"
ANTHROPIC_DEFAULT_MODEL = "claude-3-5-haiku-latest"
logger = logging.getLogger(__name__)


def infer_provider_from_api_key(api_key: str, declared: str | None = None) -> str:
    """Infer LLM provider from API key prefix; fixes mismatched provider selection."""
    key = (api_key or "").strip()
    if key.startswith("sk-ant-"):
        return "anthropic"
    if key.startswith("sk-or-v1-"):
        return "custom"
    if declared == "custom":
        return "custom"
    if declared == "anthropic":
        return "anthropic"
    if declared == "openai":
        return "openai"
    return "openai"


def normalize_llm_config(config: LLMConfig) -> LLMConfig:
    """Apply provider inference and sane default models for the resolved provider."""
    provider = infer_provider_from_api_key(config.api_key, config.provider)
    model_name = config.model_name or DEFAULT_MODEL
    embedding_model = config.embedding_model or DEFAULT_EMBEDDING

    if provider == "anthropic":
        if model_name in (DEFAULT_MODEL, "gpt-4o", "gpt-4o-mini", "gpt-4.1", "gpt-4.1-mini") or model_name.startswith("gpt-"):
            model_name = ANTHROPIC_DEFAULT_MODEL
        if embedding_model in (DEFAULT_EMBEDDING, "text-embedding-3-large", "text-embedding-ada-002") or embedding_model.startswith("text-embedding"):
            embedding_model = KEYWORD_SEARCH_EMBEDDING
    elif provider == "openai":
        if model_name.startswith("claude"):
            model_name = DEFAULT_MODEL

    return LLMConfig(
        provider=provider,
        api_key=config.api_key,
        base_url=config.base_url,
        model_name=model_name,
        embedding_model=embedding_model,
    )


def supports_vector_embeddings(config: LLMConfig) -> bool:
    config = normalize_llm_config(config)
    return config.provider in ("openai", "custom") and config.embedding_model != KEYWORD_SEARCH_EMBEDDING


def config_from_api_key_row(key: UserApiKey) -> LLMConfig | None:
    try:
        api_key = decrypt_value(key.api_key_enc)
    except InvalidToken:
        logger.warning("Skipping API key that cannot be decrypted", extra={"api_key_id": str(key.id)})
        return None

    return normalize_llm_config(
        LLMConfig(
            provider=key.provider,
            api_key=api_key,
            base_url=key.base_url,
            model_name=key.model_name or DEFAULT_MODEL,
            embedding_model=key.embedding_model or DEFAULT_EMBEDDING,
        )
    )


async def get_user_llm_config(db: AsyncSession, user_id) -> LLMConfig | None:
    result = await db.execute(
        select(UserApiKey)
        .where(UserApiKey.user_id == user_id)
        .order_by(UserApiKey.is_default.desc(), UserApiKey.created_at.desc())
    )
    keys = result.scalars().all()
    for key in keys:
        config = config_from_api_key_row(key)
        if config:
            return config
    return None


async def resolve_embeddings_config(
    db: AsyncSession,
    user_id,
    chat_config: LLMConfig,
) -> LLMConfig | None:
    """Return an OpenAI-compatible config for embeddings, or None for keyword-only RAG."""
    chat_config = normalize_llm_config(chat_config)
    if supports_vector_embeddings(chat_config):
        return chat_config

    if chat_config.provider != "anthropic":
        return None

    result = await db.execute(
        select(UserApiKey)
        .where(
            UserApiKey.user_id == user_id,
            UserApiKey.provider.in_(["openai", "custom"]),
        )
        .order_by(UserApiKey.is_default.desc(), UserApiKey.created_at.desc())
    )
    for key in result.scalars().all():
        candidate = config_from_api_key_row(key)
        if not candidate:
            continue
        if supports_vector_embeddings(candidate):
            return candidate
    return None


def create_chat_model(config: LLMConfig, temperature: float = 0.3):
    config = normalize_llm_config(config)
    if config.provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            api_key=config.api_key,
            model=config.model_name,
            temperature=temperature,
        )

    kwargs: dict = {
        "api_key": config.api_key,
        "model": config.model_name,
        "temperature": temperature,
    }
    if config.base_url:
        kwargs["base_url"] = config.base_url
    return ChatOpenAI(**kwargs)


def create_embeddings(config: LLMConfig) -> OpenAIEmbeddings:
    config = normalize_llm_config(config)
    if not supports_vector_embeddings(config):
        raise ValueError(
            "Vector embeddings require an OpenAI or OpenAI-compatible API key. "
            "Anthropic keys are used for chat only; add an OpenAI key in Settings for semantic search, "
            "or JobPilot will use keyword search automatically."
        )

    kwargs: dict = {
        "api_key": config.api_key,
        "model": config.embedding_model,
    }
    if config.base_url:
        kwargs["base_url"] = config.base_url
    return OpenAIEmbeddings(**kwargs)


async def test_api_key(config: LLMConfig) -> bool:
    config = normalize_llm_config(config)
    if config.provider == "anthropic":
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.get(
                    "https://api.anthropic.com/v1/models",
                    headers={
                        "x-api-key": config.api_key,
                        "anthropic-version": "2023-06-01",
                    },
                )
                return res.status_code == 200
        except Exception:
            return False

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
