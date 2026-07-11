import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.core.auth import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.main import app
from app.models.user import User


class _FakeResult:
    def __init__(self, rows=None):
        self._rows = rows or []

    def scalars(self):
        return self

    def all(self):
        return self._rows

    def scalar_one_or_none(self):
        return self._rows[0] if self._rows else None


class FakeDB:
    def __init__(self):
        self.added = []

    def add(self, obj):
        self.added.append(obj)

    async def flush(self):
        # Real SQLAlchemy sessions apply column defaults (id, confidence,
        # created_at, updated_at) during flush/INSERT. This stub mimics
        # that so response schemas requiring those fields can validate.
        now = datetime.now(timezone.utc)
        for obj in self.added:
            if getattr(obj, "id", None) is None:
                obj.id = uuid.uuid4()
            if getattr(obj, "confidence", None) is None:
                obj.confidence = 1.0
            if getattr(obj, "created_at", None) is None:
                obj.created_at = now
            if getattr(obj, "updated_at", None) is None:
                obj.updated_at = now

    async def commit(self):
        pass

    async def execute(self, *a, **kw):
        return _FakeResult()


def _user():
    return User(id="00000000-0000-0000-0000-000000000001", oauth_provider="dev", oauth_id="x", email="u@example.com", role="user")


@pytest.fixture
def client():
    app.dependency_overrides[get_current_user] = _user
    app.dependency_overrides[get_db] = lambda: FakeDB()
    yield TestClient(app)
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_db, None)


def test_facts_route_returns_404_when_flag_disabled(client, monkeypatch):
    monkeypatch.setattr(settings, "feature_candidate_intelligence", False)
    resp = client.get("/api/v1/candidate/facts")
    assert resp.status_code == 404


def test_facts_route_available_when_flag_enabled(client, monkeypatch):
    monkeypatch.setattr(settings, "feature_candidate_intelligence", True)
    resp = client.get("/api/v1/candidate/facts")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_fact_route_returns_created_fact(client, monkeypatch):
    monkeypatch.setattr(settings, "feature_candidate_intelligence", True)
    resp = client.post("/api/v1/candidate/facts", json={"fact_type": "skill", "payload": {"name": "Python"}})
    assert resp.status_code == 200
    assert resp.json()["fact_type"] == "skill"
