import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.core.auth import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.main import app
from app.models.audit import AuditLog
from app.models.candidate import AnswerBankEntry
from app.models.user import User
from app.schemas.candidate import AnswerBankEntryCreate, AnswerBankEntryUpdate
from app.services.candidate.answer_bank import (
    create_answer_entry,
    delete_answer_entry,
    list_answer_entries,
    update_answer_entry,
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
            if getattr(obj, "usage_count", None) is None:
                obj.usage_count = 0
            if getattr(obj, "created_at", None) is None:
                obj.created_at = now
            if getattr(obj, "updated_at", None) is None:
                obj.updated_at = now

    async def commit(self):
        pass

    async def execute(self, *a, **kw):
        return _FakeResult(self.existing)


@pytest.mark.asyncio
async def test_create_answer_entry_sets_is_sensitive_for_salary():
    db = FakeSession()
    entry = await create_answer_entry(
        db, uuid.uuid4(),
        AnswerBankEntryCreate(question_text="Expected salary?", question_category="salary", answer_text="90k"),
    )
    assert entry.is_sensitive is True


@pytest.mark.asyncio
async def test_create_answer_entry_not_sensitive_for_behavioral():
    db = FakeSession()
    entry = await create_answer_entry(
        db, uuid.uuid4(),
        AnswerBankEntryCreate(question_text="Tell me about a conflict", question_category="behavioral"),
    )
    assert entry.is_sensitive is False


@pytest.mark.asyncio
async def test_create_answer_entry_records_audit_event():
    db = FakeSession()
    await create_answer_entry(
        db, uuid.uuid4(),
        AnswerBankEntryCreate(question_text="Q", question_category="other"),
    )
    assert any(isinstance(o, AuditLog) and o.action == "answer_bank.created" for o in db.added)


@pytest.mark.asyncio
async def test_update_answer_entry_recomputes_sensitivity_on_category_change():
    user_id = uuid.uuid4()
    row = AnswerBankEntry(
        id=uuid.uuid4(), user_id=user_id, question_text="Q", question_category="behavioral",
        answer_text="", is_sensitive=False, related_fact_ids=[],
    )
    db = FakeSession(existing=[row])
    updated = await update_answer_entry(
        db, user_id, row.id, AnswerBankEntryUpdate(question_category="work_authorization")
    )
    assert updated.is_sensitive is True


@pytest.mark.asyncio
async def test_update_answer_entry_cannot_unset_sensitivity_via_payload():
    """Sensitivity is derived from category server-side; there is no client field to unset it."""
    assert "is_sensitive" not in AnswerBankEntryUpdate.model_fields


@pytest.mark.asyncio
async def test_list_answer_entries_returns_rows():
    user_id = uuid.uuid4()
    row = AnswerBankEntry(
        id=uuid.uuid4(), user_id=user_id, question_text="Q", question_category="other",
        answer_text="", is_sensitive=False, related_fact_ids=[],
    )
    db = FakeSession(existing=[row])
    assert await list_answer_entries(db, user_id) == [row]


@pytest.mark.asyncio
async def test_delete_answer_entry_removes_row():
    user_id = uuid.uuid4()
    row = AnswerBankEntry(
        id=uuid.uuid4(), user_id=user_id, question_text="Q", question_category="other",
        answer_text="", is_sensitive=False, related_fact_ids=[],
    )
    db = FakeSession(existing=[row])
    assert await delete_answer_entry(db, user_id, row.id) is True
    assert row in db.deleted


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


def test_answers_route_404_when_flag_disabled(client, monkeypatch):
    monkeypatch.setattr(settings, "feature_candidate_intelligence", False)
    assert client.get("/api/v1/candidate/answers").status_code == 404


def test_create_answer_route_marks_salary_sensitive(client, monkeypatch):
    monkeypatch.setattr(settings, "feature_candidate_intelligence", True)
    resp = client.post(
        "/api/v1/candidate/answers",
        json={"question_text": "Expected salary?", "question_category": "salary", "answer_text": "90k"},
    )
    assert resp.status_code == 200
    assert resp.json()["is_sensitive"] is True
