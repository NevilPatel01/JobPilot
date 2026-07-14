import base64
import json
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.models.candidate import CandidateDigest
from app.services.candidate.github_import import (
    GITHUB_MAX_REPOS,
    filter_repos,
    sync_github_projects,
)


def _repo(name, *, fork=False, archived=False, pushed_days_ago=10, size=100, description="A project", topics=None, stars=3):
    return {
        "full_name": f"user/{name}",
        "name": name,
        "fork": fork,
        "archived": archived,
        "pushed_at": (datetime.now(timezone.utc) - timedelta(days=pushed_days_ago)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "size": size,
        "description": description,
        "topics": topics or [],
        "stargazers_count": stars,
        "html_url": f"https://github.com/user/{name}",
    }


def test_filter_repos_excludes_forks_archived_stale_and_empty():
    repos = [
        _repo("good"),
        _repo("a-fork", fork=True),
        _repo("old", pushed_days_ago=5 * 365),
        _repo("archived", archived=True),
        _repo("empty", size=0),
    ]
    kept = filter_repos(repos)
    assert [r["name"] for r in kept] == ["good"]


def test_filter_repos_caps_at_max():
    repos = [_repo(f"r{i}") for i in range(40)]
    assert len(filter_repos(repos)) == GITHUB_MAX_REPOS


class FakeResponse:
    def __init__(self, status_code=200, payload=None, headers=None):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}
        self.headers = headers or {}

    def json(self):
        return self._payload


class FakeHTTP:
    def __init__(self, routes, rate_limited_after=None):
        self.routes = routes
        self.calls = []
        self.rate_limited_after = rate_limited_after

    async def get(self, url, **kw):
        self.calls.append(url)
        if self.rate_limited_after is not None and len(self.calls) > self.rate_limited_after:
            return FakeResponse(403, {"message": "rate limit"}, {"X-RateLimit-Remaining": "0"})
        for prefix, resp in self.routes.items():
            if url.endswith(prefix) or prefix in url:
                return resp
        return FakeResponse(404, {})


class FakeLLM:
    def __init__(self, content=None):
        self.calls = 0
        self.content = content or json.dumps(
            {
                "one_liner": "AI resume builder",
                "what_it_does": "Builds resumes",
                "tech_stack": ["Python", "Next.js"],
                "notable_features": ["multi-agent pipeline"],
                "metrics_from_readme": [],
            }
        )

    async def ainvoke(self, messages):
        self.calls += 1

        class _Msg:
            usage_metadata = {"input_tokens": 200, "output_tokens": 60}

            def __init__(self, content):
                self.content = content

        return _Msg(self.content)


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
    """execute() routes by statement's target table name via crude repr matching."""

    def __init__(self, digest=None, facts=None):
        self.added = []
        self.digest = digest
        self.facts = facts or []

    def add(self, obj):
        self.added.append(obj)
        if isinstance(obj, CandidateDigest):
            self.digest = obj

    async def flush(self):
        for obj in self.added:
            if getattr(obj, "id", None) is None:
                obj.id = uuid.uuid4()

    async def commit(self):
        pass

    async def execute(self, statement, *a, **kw):
        text = str(statement)
        if "candidate_digests" in text:
            return _FakeResult([self.digest] if self.digest else [])
        if "candidate_facts" in text:
            return _FakeResult(self.facts)
        return _FakeResult([])


def _routes(readme_sha="abc123"):
    readme = base64.b64encode(b"# JobPilot\nAn AI resume builder built with FastAPI.").decode()
    return {
        "/users/nevil/repos": FakeResponse(200, [_repo("jobpilot")]),
        "/repos/user/jobpilot/readme": FakeResponse(200, {"content": readme, "sha": readme_sha, "encoding": "base64"}),
        "/repos/user/jobpilot/languages": FakeResponse(200, {"Python": 1000, "TypeScript": 400}),
    }


@pytest.mark.asyncio
async def test_sync_returns_project_draft_with_provenance():
    db = FakeSession()
    llm = FakeLLM()
    result = await sync_github_projects(
        db, uuid.uuid4(), "nevil", http_client=FakeHTTP(_routes()), chat_model=llm
    )
    assert result.rate_limited is False
    assert len(result.draft_facts) == 1
    payload = result.draft_facts[0].payload
    assert payload["url"] == "https://github.com/user/jobpilot"
    assert payload["origin"] == "github"
    assert "Python" in payload["tech_stack"]
    assert result.draft_facts[0].source == "github_import"
    assert llm.calls == 1


@pytest.mark.asyncio
async def test_second_sync_with_unchanged_readme_makes_no_llm_calls():
    user_id = uuid.uuid4()
    db = FakeSession()
    llm1 = FakeLLM()
    await sync_github_projects(db, user_id, "nevil", http_client=FakeHTTP(_routes()), chat_model=llm1)
    assert llm1.calls == 1
    # digest row now carries sync_state with the readme sha + cached summary
    llm2 = FakeLLM()
    result2 = await sync_github_projects(db, user_id, "nevil", http_client=FakeHTTP(_routes()), chat_model=llm2)
    assert llm2.calls == 0
    assert result2.skipped_unchanged >= 0
    assert len(result2.draft_facts) == 1  # cached draft still returned for review


@pytest.mark.asyncio
async def test_sync_handles_rate_limit_gracefully():
    db = FakeSession()
    result = await sync_github_projects(
        db, uuid.uuid4(), "nevil",
        http_client=FakeHTTP(_routes(), rate_limited_after=0), chat_model=FakeLLM(),
    )
    assert result.rate_limited is True
    assert result.draft_facts == []


@pytest.mark.asyncio
async def test_sync_falls_back_to_metadata_when_llm_output_invalid():
    db = FakeSession()
    result = await sync_github_projects(
        db, uuid.uuid4(), "nevil",
        http_client=FakeHTTP(_routes()), chat_model=FakeLLM(content="not json"),
    )
    payload = result.draft_facts[0].payload
    assert payload["name"] == "jobpilot"
    assert payload["one_liner"] == "A project"  # repo description fallback


# --- routes ---

from fastapi.testclient import TestClient

from app.core.auth import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.main import app
from app.models.user import User


def _user():
    return User(id="00000000-0000-0000-0000-000000000001", oauth_provider="github", oauth_id="123", email="u@example.com", role="user")


@pytest.fixture
def client():
    app.dependency_overrides[get_current_user] = _user
    app.dependency_overrides[get_db] = lambda: FakeSession()
    yield TestClient(app)
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_db, None)


def test_github_import_route_404_when_flag_disabled(client, monkeypatch):
    monkeypatch.setattr(settings, "feature_candidate_intelligence", False)
    assert client.post("/api/v1/candidate/import/github", json={"username": "nevil"}).status_code == 404


def test_digest_route_returns_content(client, monkeypatch):
    monkeypatch.setattr(settings, "feature_candidate_intelligence", True)
    resp = client.get("/api/v1/candidate/digest/github_projects")
    assert resp.status_code == 200
    body = resp.json()
    assert "content_text" in body and "token_estimate" in body


def test_pin_route_sets_pinned_flag(client, monkeypatch):
    monkeypatch.setattr(settings, "feature_candidate_intelligence", True)
    fact = CandidateFactRow = None  # placeholder to keep flake quiet
    from app.models.candidate import CandidateFact

    now = datetime.now(timezone.utc)
    fact = CandidateFact(
        id=uuid.uuid4(), user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        fact_type="project", payload={"name": "x", "origin": "github"},
        source="github_import", verification_status="user_confirmed", superseded_by_id=None,
        is_prohibited=False, confidence=1.0, created_at=now, updated_at=now,
    )
    session = FakeSession(facts=[fact])
    session.fact_lookup = fact

    class LookupSession(FakeSession):
        async def execute(self, statement, *a, **kw):
            text = str(statement)
            if "candidate_digests" in text:
                return _FakeResult([self.digest] if self.digest else [])
            return _FakeResult([fact])

    app.dependency_overrides[get_db] = lambda: LookupSession()
    resp = client.post(f"/api/v1/candidate/facts/{fact.id}/pin")
    assert resp.status_code == 200
    assert fact.payload["pinned"] is True
