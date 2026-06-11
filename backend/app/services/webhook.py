"""Webhook delivery when a resume pipeline finishes."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

import httpx

from app.models.resume import ResumeDocument

logger = logging.getLogger(__name__)

WEBHOOK_TIMEOUT_SECONDS = 10.0


def build_pipeline_webhook_payload(
    resume: ResumeDocument,
    *,
    status: str,
    error: str | None = None,
    last_step: str | None = None,
) -> dict[str, Any]:
    return {
        "event": "pipeline.completed" if status == "completed" else "pipeline.failed",
        "resume_id": str(resume.id),
        "title": resume.title,
        "status": status,
        "last_step": last_step,
        "error": error,
    }


async def dispatch_pipeline_webhook(
    webhook_url: str,
    resume: ResumeDocument,
    *,
    status: str,
    error: str | None = None,
    last_step: str | None = None,
) -> None:
    """POST pipeline result to the caller's webhook URL. Failures are logged, not raised."""
    payload = build_pipeline_webhook_payload(
        resume,
        status=status,
        error=error,
        last_step=last_step,
    )
    try:
        async with httpx.AsyncClient(timeout=WEBHOOK_TIMEOUT_SECONDS) as client:
            response = await client.post(webhook_url, json=payload)
            response.raise_for_status()
        logger.info(
            "pipeline_webhook delivered",
            extra={
                "resume_id": str(resume.id),
                "webhook_url": webhook_url,
                "status": status,
                "http_status": response.status_code,
            },
        )
    except Exception as exc:
        logger.warning(
            "pipeline_webhook failed",
            extra={
                "resume_id": str(resume.id),
                "webhook_url": webhook_url,
                "status": status,
                "error": str(exc),
            },
        )


def get_stored_webhook_url(insights: dict | None) -> str | None:
    if not insights:
        return None
    url = insights.get("_webhook_url")
    return url if isinstance(url, str) and url.strip() else None


def store_webhook_url(insights: dict, webhook_url: str | None) -> dict:
    updated = dict(insights)
    if webhook_url:
        updated["_webhook_url"] = webhook_url
    else:
        updated.pop("_webhook_url", None)
    return updated
