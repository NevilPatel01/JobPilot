import pytest
from fastapi.testclient import TestClient

from app.core.auth import get_current_user
from app.main import app
from app.models.user import User


def _user(role: str) -> User:
    return User(
        id="00000000-0000-0000-0000-000000000001",
        oauth_provider="dev", oauth_id="x", email="u@example.com", role=role,
    )


def test_non_admin_cannot_trigger_scraper():
    """Non-moderator/admin user should receive 403 when trying to trigger scraper."""
    app.dependency_overrides[get_current_user] = lambda: _user("user")
    client = TestClient(app)
    try:
        resp = client.post("/api/v1/scraper/trigger")
        assert resp.status_code == 403
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_non_admin_cannot_update_scraper_source():
    """Non-moderator/admin user should receive 403 when trying to update scraper source."""
    app.dependency_overrides[get_current_user] = lambda: _user("user")
    client = TestClient(app)
    try:
        resp = client.patch("/api/v1/scraper/sources/remoteok", json={"enabled": False})
        assert resp.status_code == 403
    finally:
        app.dependency_overrides.pop(get_current_user, None)


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
