"""Structured logging helpers for the resume generation pipeline."""

from __future__ import annotations

import logging
from typing import Any


def log_pipeline_step(
    logger: logging.Logger,
    *,
    resume_id: str,
    step: str,
    duration_ms: int,
    status: str = "completed",
    **extra: Any,
) -> None:
    """Emit a structured pipeline step log with standard fields."""
    payload: dict[str, Any] = {
        "resume_id": resume_id,
        "step": step,
        "duration_ms": duration_ms,
        "status": status,
    }
    payload.update(extra)
    logger.info("pipeline_step %s", step, extra=payload)


def log_pipeline_event(
    logger: logging.Logger,
    *,
    resume_id: str,
    event: str,
    status: str,
    **extra: Any,
) -> None:
    """Emit a structured pipeline lifecycle log (start, complete, fail)."""
    payload: dict[str, Any] = {
        "resume_id": resume_id,
        "step": event,
        "event": event,
        "status": status,
    }
    payload.update(extra)
    logger.info("pipeline_%s", event, extra=payload)
