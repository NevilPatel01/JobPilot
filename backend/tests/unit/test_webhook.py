from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.services.webhook import (
    build_pipeline_webhook_payload,
    dispatch_pipeline_webhook,
    get_stored_webhook_url,
    store_webhook_url,
)


def _resume(**kwargs):
    defaults = {
        "id": uuid4(),
        "title": "Engineer at Acme",
        "insights_json": {"_webhook_url": "https://example.com/hook"},
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_build_pipeline_webhook_payload_completed():
    resume = _resume()
    payload = build_pipeline_webhook_payload(resume, status="completed")
    assert payload["event"] == "pipeline.completed"
    assert payload["resume_id"] == str(resume.id)
    assert payload["status"] == "completed"
    assert payload["title"] == "Engineer at Acme"


def test_build_pipeline_webhook_payload_failed():
    resume = _resume()
    payload = build_pipeline_webhook_payload(resume, status="failed", error="boom", last_step="tailor_resume")
    assert payload["event"] == "pipeline.failed"
    assert payload["error"] == "boom"
    assert payload["last_step"] == "tailor_resume"


def test_store_and_get_webhook_url():
    insights = store_webhook_url({"source_content": {}}, "https://example.com/hook")
    assert get_stored_webhook_url(insights) == "https://example.com/hook"
    cleared = store_webhook_url(insights, None)
    assert get_stored_webhook_url(cleared) is None


@pytest.mark.asyncio
async def test_dispatch_pipeline_webhook_posts_payload():
    resume = _resume()
    mock_response = SimpleNamespace(status_code=200, raise_for_status=lambda: None)
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("app.services.webhook.httpx.AsyncClient", return_value=mock_client):
        await dispatch_pipeline_webhook("https://example.com/hook", resume, status="completed")

    mock_client.post.assert_awaited_once()
    args, kwargs = mock_client.post.await_args
    assert args[0] == "https://example.com/hook"
    assert kwargs["json"]["event"] == "pipeline.completed"
