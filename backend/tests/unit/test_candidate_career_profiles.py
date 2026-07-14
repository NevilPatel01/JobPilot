import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.core.auth import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.main import app
from app.models.audit import AuditLog
from app.models.candidate import CareerProfile
from app.models.user import User
from app.schemas.candidate import CareerProfileCreate, CareerProfileUpdate
from app.services.candidate.career_profiles import (
    create_career_profile,
    delete_career_profile,
    list_career_profiles,
    set_default_career_profile,
    update_career_profile,
)


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
        self.deleted = []
        self.existing = existing or []

    def add(self, obj):
        self.added.append(obj)

    async def delete(self, obj):
        self.deleted.append(obj)

    async def flush(self):
        now = datetime.now(timezone.utc)
        for obj in self.added:
            if getattr(obj, "id", None) is None:
                obj.id = uuid.uuid4()
            if getattr(obj, "created_at", None) is None:
                obj.created_at = now
            if getattr(obj, "updated_at", None) is None:
                obj.updated_at = now

    async def commit(self):
        pass

    async def execute(self, *a, **kw):
        return _FakeResult(self.existing)


def _profile(user_id, name="Cloud", is_default=False):
    return CareerProfile(
        id=uuid.uuid4(), user_id=user_id, name=name, description="", emphasis_fact_ids=[],
        positioning_statement="", is_default=is_default,
    )


@pytest.mark.asyncio
async def test_create_career_profile_adds_row_and_audits():
    db = FakeSession()
    user_id = uuid.uuid4()
    profile = await create_career_profile(db, user_id, CareerProfileCreate(name="Cloud Support"))
    assert profile in db.added
    assert profile.user_id == user_id
    assert any(isinstance(o, AuditLog) and o.action == "career_profile.created" for o in db.added)


@pytest.mark.asyncio
async def test_create_default_profile_clears_other_defaults():
    user_id = uuid.uuid4()
    other = _profile(user_id, name="Old", is_default=True)
    db = FakeSession(existing=[other])
    await create_career_profile(db, user_id, CareerProfileCreate(name="New", is_default=True))
    assert other.is_default is False


@pytest.mark.asyncio
async def test_list_career_profiles_returns_rows():
    user_id = uuid.uuid4()
    row = _profile(user_id)
    db = FakeSession(existing=[row])
    assert await list_career_profiles(db, user_id) == [row]


@pytest.mark.asyncio
async def test_update_career_profile_changes_fields():
    user_id = uuid.uuid4()
    row = _profile(user_id)
    db = FakeSession(existing=[row])
    updated = await update_career_profile(db, user_id, row.id, CareerProfileUpdate(name="Renamed"))
    assert updated.name == "Renamed"


@pytest.mark.asyncio
async def test_delete_career_profile_removes_row():
    user_id = uuid.uuid4()
    row = _profile(user_id)
    db = FakeSession(existing=[row])
    assert await delete_career_profile(db, user_id, row.id) is True
    assert row in db.deleted


@pytest.mark.asyncio
async def test_set_default_marks_target_and_clears_others():
    user_id = uuid.uuid4()
    target = _profile(user_id, name="Target")
    other = _profile(user_id, name="Other", is_default=True)
    db = FakeSession(existing=[target, other])
    out = await set_default_career_profile(db, user_id, target.id)
    assert out.is_default is True
    assert other.is_default is False


# --- routes ---

def _user():
    return User(id="00000000-0000-0000-0000-000000000001", oauth_provider="dev", oauth_id="x", email="u@example.com", role="user")


@pytest.fixture
def client():
    app.dependency_overrides[get_current_user] = _user
    app.dependency_overrides[get_db] = lambda: FakeSession()
    yield TestClient(app)
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_db, None)


def test_career_profiles_route_404_when_flag_disabled(client, monkeypatch):
    monkeypatch.setattr(settings, "feature_candidate_intelligence", False)
    assert client.get("/api/v1/candidate/career-profiles").status_code == 404


def test_create_career_profile_route(client, monkeypatch):
    monkeypatch.setattr(settings, "feature_candidate_intelligence", True)
    resp = client.post("/api/v1/candidate/career-profiles", json={"name": "Cloud Support"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Cloud Support"
