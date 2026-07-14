import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.core.auth import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.main import app
from app.models.audit import AuditLog
from app.models.candidate import Achievement
from app.models.user import User
from app.schemas.candidate import AchievementCreate, AchievementUpdate
from app.services.candidate.achievements import (
    create_achievement,
    delete_achievement,
    list_achievements,
    set_achievement_verification,
    update_achievement,
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


@pytest.mark.asyncio
async def test_create_achievement_adds_row_with_user_id():
    db = FakeSession()
    user_id = uuid.uuid4()
    ach = await create_achievement(
        db, user_id, AchievementCreate(situation="S", task="T", action="A", result="R")
    )
    assert ach in db.added
    assert ach.user_id == user_id
    assert ach.result == "R"


@pytest.mark.asyncio
async def test_create_achievement_defaults_to_user_confirmed_for_user_entry():
    db = FakeSession()
    ach = await create_achievement(db, uuid.uuid4(), AchievementCreate(result="R"))
    assert ach.verification_status == "user_confirmed"


@pytest.mark.asyncio
async def test_create_achievement_records_audit_event():
    db = FakeSession()
    await create_achievement(db, uuid.uuid4(), AchievementCreate(result="R"))
    audit_rows = [o for o in db.added if isinstance(o, AuditLog)]
    assert len(audit_rows) == 1
    assert audit_rows[0].action == "achievement.created"


@pytest.mark.asyncio
async def test_list_achievements_returns_rows():
    user_id = uuid.uuid4()
    row = Achievement(id=uuid.uuid4(), user_id=user_id, situation="", task="", action="", result="R")
    db = FakeSession(existing=[row])
    assert await list_achievements(db, user_id) == [row]


@pytest.mark.asyncio
async def test_update_achievement_changes_fields():
    user_id = uuid.uuid4()
    row = Achievement(id=uuid.uuid4(), user_id=user_id, situation="", task="", action="", result="old")
    db = FakeSession(existing=[row])
    updated = await update_achievement(db, user_id, row.id, AchievementUpdate(result="new"))
    assert updated.result == "new"


@pytest.mark.asyncio
async def test_update_achievement_returns_none_when_missing():
    db = FakeSession(existing=[])
    assert await update_achievement(db, uuid.uuid4(), uuid.uuid4(), AchievementUpdate(result="x")) is None


@pytest.mark.asyncio
async def test_delete_achievement_removes_row_and_audits():
    user_id = uuid.uuid4()
    row = Achievement(id=uuid.uuid4(), user_id=user_id, situation="", task="", action="", result="R")
    db = FakeSession(existing=[row])
    assert await delete_achievement(db, user_id, row.id) is True
    assert row in db.deleted
    assert any(isinstance(o, AuditLog) and o.action == "achievement.deleted" for o in db.added)


@pytest.mark.asyncio
async def test_set_achievement_verification_rejects_invalid_transition():
    user_id = uuid.uuid4()
    row = Achievement(
        id=uuid.uuid4(), user_id=user_id, situation="", task="", action="", result="R",
        verification_status="contradicted",
    )
    db = FakeSession(existing=[row])
    with pytest.raises(ValueError):
        await set_achievement_verification(db, user_id, row.id, "unverified")


@pytest.mark.asyncio
async def test_set_achievement_verification_confirms_and_audits():
    user_id = uuid.uuid4()
    row = Achievement(
        id=uuid.uuid4(), user_id=user_id, situation="", task="", action="", result="R",
        verification_status="unverified",
    )
    db = FakeSession(existing=[row])
    out = await set_achievement_verification(db, user_id, row.id, "user_confirmed")
    assert out.verification_status == "user_confirmed"
    assert any(isinstance(o, AuditLog) and o.action == "achievement.verification_changed" for o in db.added)


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


def test_achievements_route_404_when_flag_disabled(client, monkeypatch):
    monkeypatch.setattr(settings, "feature_candidate_intelligence", False)
    assert client.get("/api/v1/candidate/achievements").status_code == 404


def test_create_achievement_route_returns_achievement(client, monkeypatch):
    monkeypatch.setattr(settings, "feature_candidate_intelligence", True)
    resp = client.post("/api/v1/candidate/achievements", json={"result": "Cut latency 40%"})
    assert resp.status_code == 200
    assert resp.json()["result"] == "Cut latency 40%"
