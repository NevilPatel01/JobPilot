import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.auth import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.main import app
from app.models.candidate import CandidateFact
from app.models.user import User
from app.schemas.candidate import (
    CandidateFactCreate,
    CandidateFactUpdate,
    ProjectPayload,
    validate_fact_payload,
)
from app.services.candidate.facts import create_fact, update_fact


class _FakeResult:
    def __init__(self, rows=None):
        self._rows = rows or []

    def scalars(self):
        return self

    def all(self):
        return self._rows

    def scalar_one_or_none(self):
        return self._rows[0] if self._rows else None


class FakeSession:
    def __init__(self, existing=None):
        self.added = []
        self.existing = existing or []

    def add(self, obj):
        self.added.append(obj)

    async def flush(self):
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
        return _FakeResult(self.existing)


def test_employment_payload_requires_employer_and_title():
    with pytest.raises(ValidationError):
        CandidateFactCreate(fact_type="employment", payload={"title": "Dev"})
    with pytest.raises(ValidationError):
        CandidateFactCreate(fact_type="employment", payload={"employer": "Acme"})


def test_employment_payload_normalizes_dates_to_iso_strings():
    fact = CandidateFactCreate(
        fact_type="employment",
        payload={"employer": "Acme", "title": "Dev", "start_date": "2022-01-15"},
    )
    assert fact.payload["start_date"] == "2022-01-15"
    assert isinstance(fact.payload["start_date"], str)


def test_skill_payload_requires_name():
    with pytest.raises(ValidationError):
        CandidateFactCreate(fact_type="skill", payload={"level": "expert"})


def test_project_payload_defaults():
    payload = ProjectPayload(name="JobPilot")
    assert payload.origin == "manual"
    assert payload.pinned is False
    assert payload.tech_stack == []


def test_project_fact_keeps_extra_keys():
    fact = CandidateFactCreate(fact_type="project", payload={"name": "JobPilot", "custom_note": "x"})
    assert fact.payload["custom_note"] == "x"


def test_unmodeled_fact_type_accepts_any_dict():
    fact = CandidateFactCreate(fact_type="personal", payload={"anything": {"nested": True}})
    assert fact.payload == {"anything": {"nested": True}}


def test_validate_fact_payload_rejects_bad_work_authorization():
    with pytest.raises(ValidationError):
        validate_fact_payload("work_authorization", {})


@pytest.mark.asyncio
async def test_update_fact_validates_payload_against_fact_type():
    user_id = uuid.uuid4()
    fact = CandidateFact(
        id=uuid.uuid4(), user_id=user_id, fact_type="employment",
        payload={"employer": "Acme", "title": "Dev"}, superseded_by_id=None,
    )
    db = FakeSession(existing=[fact])
    with pytest.raises(ValidationError):
        await update_fact(db, user_id, fact.id, CandidateFactUpdate(payload={"title": "only-title"}))


@pytest.mark.asyncio
async def test_create_fact_stores_normalized_payload():
    db = FakeSession()
    fact = await create_fact(
        db, uuid.uuid4(),
        CandidateFactCreate(fact_type="certification", payload={"name": "AWS SAA", "issued_date": "2024-06-01"}),
    )
    assert fact.payload["issued_date"] == "2024-06-01"


def _user():
    return User(id="00000000-0000-0000-0000-000000000001", oauth_provider="dev", oauth_id="x", email="u@example.com", role="user")


@pytest.fixture
def client():
    app.dependency_overrides[get_current_user] = _user
    app.dependency_overrides[get_db] = lambda: FakeSession()
    yield TestClient(app)
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_db, None)


def test_create_fact_route_422_on_invalid_typed_payload(client, monkeypatch):
    monkeypatch.setattr(settings, "feature_candidate_intelligence", True)
    resp = client.post("/api/v1/candidate/facts", json={"fact_type": "employment", "payload": {"title": "Dev"}})
    assert resp.status_code == 422
