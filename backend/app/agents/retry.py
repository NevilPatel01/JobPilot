import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

LLM_MAX_ATTEMPTS = 3
LLM_TIMEOUT_SECONDS = 60.0
LLM_BASE_DELAY_SECONDS = 1.0

SCRAPE_MAX_ATTEMPTS = 2
SCRAPE_TIMEOUT_SECONDS = 30.0
SCRAPE_BASE_DELAY_SECONDS = 2.0


async def with_retry(
    operation: Callable[[], Awaitable[T]],
    *,
    max_attempts: int,
    timeout_seconds: float,
    base_delay_seconds: float,
    label: str,
) -> T:
    last_error: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            return await asyncio.wait_for(operation(), timeout=timeout_seconds)
        except Exception as e:
            last_error = e
            if attempt >= max_attempts:
                break
            delay = base_delay_seconds * (2 ** (attempt - 1))
            logger.warning("%s failed (attempt %s/%s): %s — retry in %.1fs", label, attempt, max_attempts, e, delay)
            await asyncio.sleep(delay)
    raise last_error  # type: ignore[misc]


async def invoke_llm(llm, messages: list) -> object:
    async def _call():
        return await llm.ainvoke(messages)

    return await with_retry(
        _call,
        max_attempts=LLM_MAX_ATTEMPTS,
        timeout_seconds=LLM_TIMEOUT_SECONDS,
        base_delay_seconds=LLM_BASE_DELAY_SECONDS,
        label="LLM invoke",
    )
