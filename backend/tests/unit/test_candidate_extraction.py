import json
import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.core.auth import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.main import app
from app.models.audit import AuditLog
from app.models.candidate import CandidateFact
from app.models.user import User
from app.services.candidate.extraction import EXTRACTION_PROMPT_VERSION, extract_facts_from_resume_text
from app.services.candidate.imports import confirm_draft_facts

RESUME_TEXT = (
    "Nevil Patel. Support Analyst at Acme Corp since 2022. "
    "Built JobPilot, an AI resume builder. Skills: Python, AWS."
)


class FakeLLM:
    """Returns queued responses; mirrors langchain's ainvoke contract."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    async def ainvoke(self, messages):
        self.calls += 1
        content = self.responses.pop(0)

        class _Msg:
            usage_metadata = {"input_tokens": 100, "output_tokens": 50}

            def __init__(self, content):
                self.content = content

        return _Msg(content)


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
            if getattr(obj, "created_at", None) is None:
                obj.created_at = now

    async def commit(self):
        pass

    async def execute(self, *a, **kw):
        return _FakeResult(self.existing)


def _valid_response():
    return json.dumps(
        {
            "facts": [
                {
                    "fact_type": "employment",
                    "payload": {"employer": "Acme Corp", "title": "Support Analyst"},
                    "source_excerpt": "Support Analyst at Acme Corp",
                },
                {
                    "fact_type": "skill",
                    "payload": {"name": "Python"},
                    "source_excerpt": "Skills: Python",
                },
            ]
        }
    )


@pytest.mark.asyncio
async def test_extraction_returns_validated_drafts():
    db = FakeSession()
    llm = FakeLLM([_valid_response()])
    result = await extract_facts_from_resume_text(db, uuid.uuid4(), RESUME_TEXT, chat_model=llm)
    assert len(result.draft_facts) == 2
    assert result.draft_facts[0].payload["employer"] == "Acme Corp"
    assert result.draft_facts[0].source == "resume_upload"


@pytest.mark.asyncio
async def test_extraction_rejects_hallucinated_excerpt():
    db = FakeSession()
    response = json.dumps(
        {
            "facts": [
                {
                    "fact_type": "employment",
                    "payload": {"employer": "Google", "title": "Staff Engineer"},
                    "source_excerpt": "Staff Engineer at Google",
                }
            ]
        }
    )
    llm = FakeLLM([response])
    result = await extract_facts_from_resume_text(db, uuid.uuid4(), RESUME_TEXT, chat_model=llm)
    assert result.draft_facts == []
    assert result.rejected == 1


@pytest.mark.asyncio
async def test_extraction_retries_once_on_invalid_json_then_succeeds():
    db = FakeSession()
    llm = FakeLLM(["not json at all", _valid_response()])
    result = await extract_facts_from_resume_text(db, uuid.uuid4(), RESUME_TEXT, chat_model=llm)
    assert llm.calls == 2
    assert len(result.draft_facts) == 2


@pytest.mark.asyncio
async def test_extraction_gives_up_after_retry_and_returns_warning():
    db = FakeSession()
    llm = FakeLLM(["not json", "still not json"])
    result = await extract_facts_from_resume_text(db, uuid.uuid4(), RESUME_TEXT, chat_model=llm)
    assert result.draft_facts == []
    assert result.warning


@pytest.mark.asyncio
async def test_extraction_logs_audit_event_with_model_and_tokens():
    db = FakeSession()
    llm = FakeLLM([_valid_response()])
    await extract_facts_from_resume_text(db, uuid.uuid4(), RESUME_TEXT, chat_model=llm, model_name="gpt-test")
    audit_rows = [o for o in db.added if isinstance(o, AuditLog)]
    assert len(audit_rows) == 1
    assert audit_rows[0].action == "candidate_fact.extraction"
    assert audit_rows[0].prompt_version == EXTRACTION_PROMPT_VERSION
    assert audit_rows[0].model_name == "gpt-test"
    assert audit_rows[0].after_json["input_tokens"] == 100


@pytest.mark.asyncio
async def test_confirm_draft_facts_persists_unverified():
    db = FakeSession()
    result = await confirm_draft_facts(
        db, uuid.uuid4(),
        [{"fact_type": "skill", "payload": {"name": "AWS"}, "source": "resume_upload"}],
    )
    assert result["created"] == 1
    facts = [o for o in db.added if isinstance(o, CandidateFact)]
    assert facts[0].verification_status == "unverified"


@pytest.mark.asyncio
async def test_confirm_github_project_supersedes_existing_by_url():
    user_id = uuid.uuid4()
    existing = CandidateFact(
        id=uuid.uuid4(), user_id=user_id, fact_type="project",
        payload={"name": "JobPilot", "url": "https://github.com/x/jobpilot", "origin": "github"},
        source="github_import", superseded_by_id=None,
    )
    db = FakeSession(existing=[existing])
    result = await confirm_draft_facts(
        db, user_id,
        [{
            "fact_type": "project",
            "payload": {"name": "JobPilot", "url": "https://github.com/x/jobpilot", "one_liner": "updated", "origin": "github"},
            "source": "github_import",
        }],
    )
    assert result["superseded"] == 1
    assert existing.superseded_by_id is not None


def _user():
    return User(id="00000000-0000-0000-0000-000000000001", oauth_provider="dev", oauth_id="x", email="u@example.com", role="user")


@pytest.fixture
def client():
    app.dependency_overrides[get_current_user] = _user
    app.dependency_overrides[get_db] = lambda: FakeSession()
    yield TestClient(app)
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_db, None)


def test_resume_text_import_route_404_when_flag_disabled(client, monkeypatch):
    monkeypatch.setattr(settings, "feature_candidate_intelligence", False)
    assert client.post("/api/v1/candidate/import/resume-text", json={"text": "x"}).status_code == 404


def test_confirm_import_route_returns_counts(client, monkeypatch):
    monkeypatch.setattr(settings, "feature_candidate_intelligence", True)
    resp = client.post(
        "/api/v1/candidate/import/confirm",
        json={"facts": [{"fact_type": "skill", "payload": {"name": "AWS"}, "source": "resume_upload"}]},
    )
    assert resp.status_code == 200
    assert resp.json()["created"] == 1
