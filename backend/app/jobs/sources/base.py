from abc import ABC, abstractmethod

import httpx

from app.jobs.pipeline.contracts import NormalizedJob


class SourceUnavailable(RuntimeError):
    """Source cannot run until its configuration changes."""


class SourceRateLimited(RuntimeError):
    """Source quota is exhausted; remaining lower-priority queries should stop."""


class SourceAuthError(SourceUnavailable):
    """Source credentials are missing or rejected."""


class CanadianJobSource(ABC):
    source_name: str
    display_name: str
    requires_credentials: bool = False
    rate_limit_label: str | None = None

    def __init__(self, client: httpx.AsyncClient | None = None):
        self._client = client

    @property
    @abstractmethod
    def credentials_available(self) -> bool:
        ...

    @property
    def credential_status(self) -> str:
        if not self.requires_credentials:
            return "not_required"
        return "configured" if self.credentials_available else "missing"

    @abstractmethod
    async def fetch(self, query: str, city: str, max_pages: int = 1) -> list[NormalizedJob]:
        ...

    async def __aenter__(self):
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=20, follow_redirects=True)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self._client:
            await self._client.aclose()
        self._client = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError("Use source as an async context manager")
        return self._client
