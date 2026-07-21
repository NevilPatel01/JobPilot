from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.core.auth import get_current_user
from app.core.database import get_db
from app.main import app
from app.models.job_intelligence import JobSourceConfig
from app.models.user import User


def _user(role: str) -> User:
    return User(
        id="00000000-0000-0000-0000-000000000001",
        oauth_provider="dev", oauth_id="x", email="u@example.com", role=role,
    )


async def _fake_db():
    session = AsyncMock()
    session.commit = AsyncMock()
    yield session


def test_non_admin_cannot_trigger_scraper():
    """Non-moderator/admin user should receive 403 when trying to trigger scraper."""
    app.dependency_overrides[get_current_user] = lambda: _user("user")
    client = TestClient(app)
    try:
        resp = client.post("/api/v1/scraper/trigger")
        assert resp.status_code == 403
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_authenticated_user_can_update_scraper_source(monkeypatch):
    """Any authenticated user may toggle scraper sources (no moderator gate)."""
    config = JobSourceConfig(name="remoteok", enabled=True, rate_limit=None)

    async def fake_ensure(_session):
        return {"remoteok": config}

    monkeypatch.setattr("app.api.routes.scraper.ensure_source_configs", fake_ensure)
    app.dependency_overrides[get_current_user] = lambda: _user("user")
    app.dependency_overrides[get_db] = _fake_db
    client = TestClient(app)
    try:
        resp = client.patch("/api/v1/scraper/sources/remoteok", json={"enabled": False})
        assert resp.status_code == 200, resp.text
        assert resp.json() == {"source": "remoteok", "enabled": False}
        assert config.enabled is False
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_admin_can_trigger_scraper_debounce_or_success():
    """Admin user should get 200 or 429 (not 403) when triggering scraper."""
    app.dependency_overrides[get_current_user] = lambda: _user("admin")
    client = TestClient(app)
    try:
        resp = client.post("/api/v1/scraper/trigger")
        assert resp.status_code in (200, 429), f"Expected 200 or 429, got {resp.status_code}"
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_moderator_can_trigger_scraper_debounce_or_success():
    """Moderator user should get 200 or 429 (not 403) when triggering scraper."""
    app.dependency_overrides[get_current_user] = lambda: _user("moderator")
    client = TestClient(app)
    try:
        resp = client.post("/api/v1/scraper/trigger")
        assert resp.status_code in (200, 429), f"Expected 200 or 429, got {resp.status_code}"
    finally:
        app.dependency_overrides.pop(get_current_user, None)
