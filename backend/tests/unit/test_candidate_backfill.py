import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.core.auth import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.main import app
from app.models.candidate import CandidateFact
from app.models.user import User
from app.services.candidate.backfill import (
    legacy_profile_to_draft_facts,
    payload_hash,
    run_legacy_backfill,
)

LEGACY_CONTENT = {
    "contact": {"full_name": "Nevil", "email": "n@example.com", "phone": "", "location": "Calgary"},
    "summary": "IT support specialist",
    "experience": [
        {
            "company": "Acme", "title": "Support Analyst", "location": "Calgary",
            "start_date": "2022-01-01", "end_date": "", "bullets": ["Resolved 50 tickets/week"],
        }
    ],
    "education": [
        {"institution": "SAIT", "degree": "Diploma", "location": "", "start_date": "", "end_date": "2021-05-01"}
    ],
    "projects": [
        {"name": "JobPilot", "url": "", "github_url": "https://github.com/x/jobpilot", "bullets": ["AI resume builder"]}
    ],
    "skills": [
        {"name": "Cloud", "skills": ["AWS", "Docker"]},
    ],
}


def test_mapper_creates_employment_fact_from_experience():
    drafts = legacy_profile_to_draft_facts(LEGACY_CONTENT, [], None)
    employment = [d for d in drafts if d.fact_type == "employment"]
    assert len(employment) == 1
    assert employment[0].payload["employer"] == "Acme"
    assert employment[0].payload["start_date"] == "2022-01-01"
    assert employment[0].source == "inferred"


def test_mapper_keeps_unparseable_dates_as_text():
    content = {
        "experience": [
            {"company": "Acme", "title": "Dev", "start_date": "Jan 2022", "end_date": "Present", "bullets": []}
        ]
    }
    drafts = legacy_profile_to_draft_facts(content, [], None)
    payload = drafts[0].payload
    assert "start_date" not in payload
    assert payload["start_date_text"] == "Jan 2022"


def test_mapper_creates_project_fact_with_repo_url():
    drafts = legacy_profile_to_draft_facts(LEGACY_CONTENT, [], None)
    projects = [d for d in drafts if d.fact_type == "project"]
    assert projects[0].payload["url"] == "https://github.com/x/jobpilot"
    assert projects[0].payload["origin"] == "manual"


def test_mapper_merges_and_dedupes_skills():
    drafts = legacy_profile_to_draft_facts(LEGACY_CONTENT, ["aws", "Python"], None)
    skills = sorted(d.payload["name"] for d in drafts if d.fact_type == "skill")
    assert skills == ["AWS", "Docker", "Python"]  # aws deduped case-insensitively


def test_mapper_creates_work_authorization_fact_from_prefs():
    drafts = legacy_profile_to_draft_facts({}, [], "work_permit")
    auth = [d for d in drafts if d.fact_type == "work_authorization"]
    assert auth[0].payload["status"] == "work_permit"


def test_payload_hash_is_order_insensitive():
    assert payload_hash("skill", {"a": 1, "b": 2}) == payload_hash("skill", {"b": 2, "a": 1})


class _FakeResult:
    def __init__(self, rows=None):
        self._rows = rows or []

    def scalars(self):
        return self

    def all(self):
        return self._rows

    def scalar_one_or_none(self):
        return self._rows[0] if self._rows else None


class QueuedSession:
    """FakeSession whose execute() pops queued results (one per query)."""

    def __init__(self, queued):
        self.queued = list(queued)
        self.added = []

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
        rows = self.queued.pop(0) if self.queued else []
        return _FakeResult(rows)


class _ProfileRow:
    def __init__(self, content):
        self.content_json = content


class _Prefs:
    work_authorization = "work_permit"


@pytest.mark.asyncio
async def test_run_legacy_backfill_creates_facts():
    # query order: profile row, scoring prefs, user, existing facts
    db = QueuedSession([[_ProfileRow(LEGACY_CONTENT)], [_Prefs()], [], []])
    result = await run_legacy_backfill(db, uuid.uuid4())
    assert result["created"] > 0
    assert result["skipped"] == 0
    created_facts = [o for o in db.added if isinstance(o, CandidateFact)]
    assert any(f.fact_type == "employment" for f in created_facts)
    assert all(f.verification_status == "unverified" for f in created_facts)


@pytest.mark.asyncio
async def test_run_legacy_backfill_is_idempotent():
    user_id = uuid.uuid4()
    db1 = QueuedSession([[_ProfileRow(LEGACY_CONTENT)], [_Prefs()], [], []])
    first = await run_legacy_backfill(db1, user_id)
    existing = [o for o in db1.added if isinstance(o, CandidateFact)]
    db2 = QueuedSession([[_ProfileRow(LEGACY_CONTENT)], [_Prefs()], [], existing])
    second = await run_legacy_backfill(db2, user_id)
    assert second["created"] == 0
    assert second["skipped"] == first["created"]


def _user():
    return User(id="00000000-0000-0000-0000-000000000001", oauth_provider="dev", oauth_id="x", email="u@example.com", role="user")


@pytest.fixture
def client():
    app.dependency_overrides[get_current_user] = _user
    app.dependency_overrides[get_db] = lambda: QueuedSession([[], [], [], []])
    yield TestClient(app)
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_db, None)


def test_legacy_import_route_404_when_flag_disabled(client, monkeypatch):
    monkeypatch.setattr(settings, "feature_candidate_intelligence", False)
    assert client.post("/api/v1/candidate/import/legacy-profile").status_code == 404


def test_legacy_import_route_returns_counts(client, monkeypatch):
    monkeypatch.setattr(settings, "feature_candidate_intelligence", True)
    resp = client.post("/api/v1/candidate/import/legacy-profile")
    assert resp.status_code == 200
    assert resp.json() == {"created": 0, "skipped": 0}


def test_migration_009_adds_github_import_source():
    import pathlib

    text = pathlib.Path("alembic/versions/009_github_projects.py").read_text()
    assert "github_import" in text
    assert "candidate_digests" in text
