"""Cost-aware model selection for BYOK providers."""

from __future__ import annotations

import re

import httpx

from app.services.llm.client import KEYWORD_SEARCH_EMBEDDING, LLMConfig, infer_provider_from_api_key, normalize_llm_config

AUTO = "auto"

# Preferred chat models ordered by cost efficiency (cheapest first).
OPENAI_CHAT_PRESETS = [
    "gpt-4o-mini",
    "gpt-4.1-mini",
    "gpt-4o",
    "gpt-4.1",
    "o1-mini",
    "o3-mini",
]

OPENAI_EMBEDDING_PRESETS = [
    "text-embedding-3-small",
    "text-embedding-3-large",
    "text-embedding-ada-002",
]

ANTHROPIC_CHAT_PRESETS = [
    "claude-3-5-haiku-latest",
    "claude-3-5-sonnet-latest",
    "claude-3-opus-latest",
    "claude-3-haiku-20240307",
]

CHAT_EXCLUDE = re.compile(
    r"(embed|embedding|tts|whisper|dall-e|davinci|moderation|transcribe|realtime|audio|image)",
    re.I,
)
EMBED_INCLUDE = re.compile(r"embed", re.I)
COST_HINT = re.compile(r"(mini|haiku|small|nano|lite|flash)", re.I)


def _api_base(config: LLMConfig) -> str:
    if config.provider == "anthropic":
        return "https://api.anthropic.com"
    return (config.base_url or "https://api.openai.com/v1").rstrip("/")


async def fetch_openai_models(config: LLMConfig) -> list[str]:
    base = _api_base(config)
    async with httpx.AsyncClient(timeout=15.0) as client:
        res = await client.get(
            f"{base}/models",
            headers={"Authorization": f"Bearer {config.api_key}"},
        )
        if res.status_code != 200:
            return []
        data = res.json()
        return [m.get("id", "") for m in data.get("data", []) if m.get("id")]


async def fetch_anthropic_models(config: LLMConfig) -> list[str]:
    async with httpx.AsyncClient(timeout=15.0) as client:
        res = await client.get(
            "https://api.anthropic.com/v1/models",
            headers={
                "x-api-key": config.api_key,
                "anthropic-version": "2023-06-01",
            },
        )
        if res.status_code != 200:
            return ANTHROPIC_CHAT_PRESETS.copy()
        data = res.json()
        return [m.get("id", "") for m in data.get("data", []) if m.get("id")]


async def list_provider_models(config: LLMConfig) -> dict[str, list[str]]:
    config = normalize_llm_config(config)
    if config.provider == "anthropic":
        all_models = await fetch_anthropic_models(config)
        chat = [m for m in all_models if not CHAT_EXCLUDE.search(m)]
        return {
            "chat_models": chat or ANTHROPIC_CHAT_PRESETS.copy(),
            "embedding_models": [KEYWORD_SEARCH_EMBEDDING],
        }

    all_models = await fetch_openai_models(config)
    chat = [m for m in all_models if not CHAT_EXCLUDE.search(m)]
    embed = [m for m in all_models if EMBED_INCLUDE.search(m)]
    if not chat:
        chat = OPENAI_CHAT_PRESETS.copy()
    if not embed:
        embed = OPENAI_EMBEDDING_PRESETS.copy()
    return {"chat_models": chat, "embedding_models": embed}


def _score_model(model_id: str, presets: list[str]) -> tuple[int, int]:
    """Lower score = better (cheaper). Preset order breaks ties."""
    preset_rank = presets.index(model_id) if model_id in presets else len(presets) + 10
    cost_bonus = 0 if COST_HINT.search(model_id) else 5
    return (cost_bonus, preset_rank)


def pick_chat_model(models: list[str], provider: str) -> str:
    presets = ANTHROPIC_CHAT_PRESETS if provider == "anthropic" else OPENAI_CHAT_PRESETS
    candidates = [m for m in models if m and not CHAT_EXCLUDE.search(m)]
    if not candidates:
        return presets[0]
    return min(candidates, key=lambda m: _score_model(m, presets))


def pick_embedding_model(models: list[str], provider: str) -> str:
    if provider == "anthropic":
        return KEYWORD_SEARCH_EMBEDDING
    candidates = [m for m in models if m and EMBED_INCLUDE.search(m)]
    if not candidates:
        return OPENAI_EMBEDDING_PRESETS[0]
    return min(candidates, key=lambda m: _score_model(m, OPENAI_EMBEDDING_PRESETS))


async def auto_select_models(config: LLMConfig) -> dict[str, str]:
    config = normalize_llm_config(config)
    listed = await list_provider_models(config)
    chat = pick_chat_model(listed["chat_models"], config.provider)
    embed = pick_embedding_model(listed["embedding_models"], config.provider)
    if embed == KEYWORD_SEARCH_EMBEDDING:
        reason = (
            f"Selected {chat} for chat. Semantic search will use keyword matching "
            f"(Anthropic does not provide embeddings). Add an OpenAI key in Settings for vector search."
        )
    else:
        reason = (
            f"Selected {chat} for chat and {embed} for embeddings "
            f"(cost-efficient defaults for {config.provider})"
        )
    return {"model_name": chat, "embedding_model": embed, "reason": reason}


def resolve_stored_model(value: str | None, default: str) -> str:
    if not value or value == AUTO:
        return default
    return value
