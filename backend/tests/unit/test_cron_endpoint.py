import pytest
from fastapi.testclient import TestClient

from app.core.config import normalize_database_url, settings
from app.main import app


def test_normalize_database_url_adds_asyncpg():
    raw = "postgresql://user:pass@host/db?sslmode=require"
    assert normalize_database_url(raw) == "postgresql+asyncpg://user:pass@host/db?sslmode=require"


def test_cron_scrape_requires_secret_configured(monkeypatch):
    monkeypatch.setattr(settings, "cron_secret", "")
    client = TestClient(app)
    response = client.post("/api/v1/internal/cron/scrape")
    assert response.status_code == 404


def test_cron_scrape_rejects_invalid_token(monkeypatch):
    monkeypatch.setattr(settings, "cron_secret", "test-cron-secret")
    client = TestClient(app)
    response = client.post(
        "/api/v1/internal/cron/scrape",
        headers={"Authorization": "Bearer wrong"},
    )
    assert response.status_code == 401
