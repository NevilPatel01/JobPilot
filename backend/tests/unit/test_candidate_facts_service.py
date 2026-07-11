import uuid

import pytest

from app.models.candidate import CandidateFact
from app.schemas.candidate import CandidateFactCreate
from app.services.candidate.facts import (
    create_fact, is_valid_verification_transition, list_active_facts, set_verification_status, supersede_fact,
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
        self.existing = existing or []

    def add(self, obj):
        self.added.append(obj)

    async def flush(self):
        pass

    async def commit(self):
        pass

    async def execute(self, *a, **kw):
        return _FakeResult(self.existing)


def test_is_valid_verification_transition_allows_unverified_to_confirmed():
    assert is_valid_verification_transition("unverified", "user_confirmed") is True


def test_is_valid_verification_transition_rejects_contradicted_to_unverified():
    assert is_valid_verification_transition("contradicted", "unverified") is False


def test_is_valid_verification_transition_allows_confirmed_to_contradicted():
    assert is_valid_verification_transition("user_confirmed", "contradicted") is True


@pytest.mark.asyncio
async def test_create_fact_adds_row_with_user_id():
    db = FakeSession()
    user_id = uuid.uuid4()
    fact = await create_fact(db, user_id, CandidateFactCreate(fact_type="skill", payload={"name": "Python"}))
    assert fact in db.added
    assert fact.user_id == user_id
    assert fact.fact_type == "skill"


@pytest.mark.asyncio
async def test_list_active_facts_excludes_prohibited_by_default():
    user_id = uuid.uuid4()
    prohibited = CandidateFact(id=uuid.uuid4(), user_id=user_id, fact_type="employment", payload={}, is_prohibited=True, superseded_by_id=None)
    visible = CandidateFact(id=uuid.uuid4(), user_id=user_id, fact_type="employment", payload={}, is_prohibited=False, superseded_by_id=None)
    db = FakeSession(existing=[prohibited, visible])
    result = await list_active_facts(db, user_id)
    assert prohibited not in result
    assert visible in result


@pytest.mark.asyncio
async def test_list_active_facts_can_include_prohibited_when_requested():
    user_id = uuid.uuid4()
    prohibited = CandidateFact(id=uuid.uuid4(), user_id=user_id, fact_type="employment", payload={}, is_prohibited=True, superseded_by_id=None)
    db = FakeSession(existing=[prohibited])
    result = await list_active_facts(db, user_id, exclude_prohibited=False)
    assert prohibited in result


@pytest.mark.asyncio
async def test_supersede_fact_creates_new_row_and_links_old_row():
    user_id = uuid.uuid4()
    old = CandidateFact(id=uuid.uuid4(), user_id=user_id, fact_type="skill", payload={"name": "Old"}, superseded_by_id=None)
    db = FakeSession(existing=[old])
    new = await supersede_fact(db, user_id, old.id, {"name": "New"})
    assert new in db.added
    assert new.payload == {"name": "New"}
    assert old.superseded_by_id == new.id
