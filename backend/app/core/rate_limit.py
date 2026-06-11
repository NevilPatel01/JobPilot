"""Rate limiting for the public documents API."""

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings


def api_key_or_ip(request: Request) -> str:
    """Rate-limit key: prefer API token, fall back to client IP."""
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"api:{api_key}"
    return f"ip:{get_remote_address(request)}"


limiter = Limiter(
    key_func=api_key_or_ip,
    default_limits=[settings.public_api_rate_limit_default],
    storage_uri=settings.rate_limit_storage_uri,
)
