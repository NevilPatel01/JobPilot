import pytest

from app.services.llm.client import (
    ANTHROPIC_DEFAULT_MODEL,
    KEYWORD_SEARCH_EMBEDDING,
    LLMConfig,
    infer_provider_from_api_key,
    normalize_llm_config,
    supports_vector_embeddings,
)


def test_infer_provider_detects_anthropic_key():
    assert infer_provider_from_api_key("sk-ant-api03-abc", "openai") == "anthropic"


def test_infer_provider_respects_openai_selection_for_sk_keys():
    assert infer_provider_from_api_key("sk-proj-abc", "openai") == "openai"


def test_normalize_anthropic_config_uses_claude_model_and_keyword_embeddings():
    config = normalize_llm_config(
        LLMConfig(
            provider="openai",
            api_key="sk-ant-api03-test",
            base_url=None,
            model_name="gpt-4o-mini",
            embedding_model="text-embedding-3-small",
        )
    )
    assert config.provider == "anthropic"
    assert config.model_name == ANTHROPIC_DEFAULT_MODEL
    assert config.embedding_model == KEYWORD_SEARCH_EMBEDDING
    assert supports_vector_embeddings(config) is False


def test_normalize_openai_config_keeps_embedding_model():
    config = normalize_llm_config(
        LLMConfig(
            provider="openai",
            api_key="sk-proj-test",
            base_url=None,
            model_name="gpt-4o-mini",
            embedding_model="text-embedding-3-small",
        )
    )
    assert config.provider == "openai"
    assert supports_vector_embeddings(config) is True


def test_create_embeddings_rejects_anthropic_key():
    from app.services.llm.client import create_embeddings

    config = normalize_llm_config(
        LLMConfig(
            provider="anthropic",
            api_key="sk-ant-api03-test",
            base_url=None,
            model_name=ANTHROPIC_DEFAULT_MODEL,
            embedding_model=KEYWORD_SEARCH_EMBEDDING,
        )
    )
    with pytest.raises(ValueError, match="Vector embeddings require"):
        create_embeddings(config)
