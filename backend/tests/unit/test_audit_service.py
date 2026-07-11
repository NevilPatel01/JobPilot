import uuid

import pytest

from app.services.audit import record_audit_event


class _FakeResult:
    def scalar_one_or_none(self):
        return None


class FakeSession:
    def __init__(self):
        self.added = []

    def add(self, obj):
        self.added.append(obj)

    async def flush(self):
        pass

    async def commit(self):
        pass

    async def execute(self, *a, **kw):
        return _FakeResult()


@pytest.mark.asyncio
async def test_record_audit_event_creates_row_with_all_fields():
    db = FakeSession()
    user_id = uuid.uuid4()
    entity_id = str(uuid.uuid4())

    row = await record_audit_event(
        db,
        user_id=user_id,
        action="candidate_fact.created",
        entity_type="candidate_facts",
        entity_id=entity_id,
        after={"fact_type": "skill"},
        model_name="gpt-4o-mini",
        prompt_version="v1",
        confidence=0.9,
    )

    assert row in db.added
    assert row.user_id == user_id
    assert row.action == "candidate_fact.created"
    assert row.entity_type == "candidate_facts"
    assert row.entity_id == entity_id
    assert row.after_json == {"fact_type": "skill"}
    assert row.model_name == "gpt-4o-mini"
    assert row.confidence == 0.9


@pytest.mark.asyncio
async def test_record_audit_event_defaults_optional_fields_to_none():
    db = FakeSession()
    row = await record_audit_event(
        db, user_id=None, action="scraper.triggered", entity_type="job_sources", entity_id="remoteok",
    )
    assert row.before_json is None
    assert row.model_name is None
