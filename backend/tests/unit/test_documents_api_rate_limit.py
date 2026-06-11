from unittest.mock import MagicMock

from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.rate_limit import limiter


def test_documents_create_route_has_stricter_limit():
    from app.api.routes import documents_api

    create_limit = limiter._route_limits["app.api.routes.documents_api.api_create_resume"][0].limit
    get_limit = limiter._route_limits["app.api.routes.documents_api.api_get_resume"][0].limit
    assert create_limit.amount == 10
    assert get_limit.amount == 60
    assert create_limit.amount < get_limit.amount
    assert len(documents_api.router.routes) >= 5


def test_rate_limit_exceeded_is_registered():
    from app.main import app

    assert RateLimitExceeded in app.exception_handlers


def test_limiter_uses_api_key_key_func():
    request = MagicMock()
    request.headers = {"X-API-Key": "jp_abc"}
    assert limiter._key_func(request) == "api:jp_abc"
