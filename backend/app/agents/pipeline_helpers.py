"""Shared utilities and state container for the resume generation pipeline."""

import logging
import time
from typing import Awaitable, Callable, TypeVar

from app.core.pipeline_logging import log_pipeline_step
from app.models.resume import AgentRun
from app.sockets.chat import sio

logger = logging.getLogger(__name__)
T = TypeVar("T")


class PipelineState(dict):
    """Typed-ish pipeline state bag."""


async def emit(resume_id: str, event: str, data: dict) -> None:
    await sio.emit(event, data, room=f"resume:{resume_id}")


async def run_step(
    db,
    resume_id,
    agent_type: str,
    status: str,
    steps: dict | None = None,
    error: str | None = None,
    model_name: str | None = None,
    prompt_version: str | None = None,
    confidence: float | None = None,
) -> None:
    run = AgentRun(
        resume_id=resume_id,
        agent_type=agent_type,
        status=status,
        steps_json=steps,
        error=error,
        model_name=model_name,
        prompt_version=prompt_version,
        confidence=confidence,
    )
    db.add(run)
    await db.flush()


async def fail_step(db, resume_id, step: str, error: str) -> None:
    await run_step(db, resume_id, step, "failed", error=error)
    await emit(resume_id, "agent_step", {"step": step, "status": "failed", "error": error})


async def run_timed_step(
    resume_id: str,
    step: str,
    runner: Callable[[], Awaitable[T]],
) -> T:
    started = time.perf_counter()
    try:
        result = await runner()
    except Exception:
        duration_ms = int((time.perf_counter() - started) * 1000)
        log_pipeline_step(logger, resume_id=resume_id, step=step, duration_ms=duration_ms, status="failed")
        raise
    duration_ms = int((time.perf_counter() - started) * 1000)
    log_pipeline_step(logger, resume_id=resume_id, step=step, duration_ms=duration_ms, status="completed")
    return result
