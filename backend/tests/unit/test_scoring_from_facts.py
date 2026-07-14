import uuid
from datetime import datetime, timezone

import pytest

from app.core.config import settings
from app.models.candidate import CandidateFact
from app.models.user import User
from app.services.candidate.resume_source import build_resume_content_from_facts, facts_candidate_inputs


def _fact(user_id, fact_type, payload, *, confirmed=True, prohibited=False):
    now = datetime.now(timezone.utc)
    return CandidateFact(
        id=uuid.uuid4(), user_id=user_id, fact_type=fact_type, payload=payload,
        source="user_entered",
        verification_status="user_confirmed" if confirmed else "unverified",
        is_prohibited=prohibited, superseded_by_id=None, confidence=1.0,
        created_at=now, updated_at=now,
    )


def _facts(user_id):
    return [
        _fact(user_id, "contact", {"full_name": "Nevil", "email": "n@x.com", "location": "Calgary"}),
        _fact(user_id, "employment", {
            "employer": "Acme", "title": "Support Analyst",
            "start_date": "2022-01-01", "end_date": "2024-01-01",
            "summary": "Resolved tickets. Automated onboarding.",
        }),
        _fact(user_id, "education", {"institution": "SAIT", "credential": "Diploma"}),
        _fact(user_id, "skill", {"name": "Python"}),
        _fact(user_id, "skill", {"name": "AWS"}),
        _fact(user_id, "work_authorization", {"status": "permanent_resident", "country": "CA"}),
        _fact(user_id, "project", {
            "name": "JobPilot", "url": "https://github.com/x/jobpilot",
            "one_liner": "AI resume builder", "tech_stack": ["Python"],
            "highlights": ["multi-agent pipeline"], "stars": 4, "origin": "github",
        }),
    ]


class _FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def scalars(self):
        return self

    def all(self):
        return self._rows

    def scalar_one_or_none(self):
        return self._rows[0] if self._rows else None


class FactsSession:
    def __init__(self, facts):
        self.facts = facts

    async def execute(self, *a, **kw):
        return _FakeResult(self.facts)

    async def flush(self):
        pass


@pytest.mark.asyncio
async def test_facts_candidate_inputs_derives_skills_years_and_auth():
    user_id = uuid.uuid4()
    db = FactsSession(_facts(user_id))
    inputs = await facts_candidate_inputs(db, user_id)
    assert inputs is not None
    assert "Python" in inputs.skills and "AWS" in inputs.skills
    assert inputs.years_experience == 2.0
    assert inputs.work_authorization == "permanent_resident"


@pytest.mark.asyncio
async def test_facts_candidate_inputs_none_when_no_facts():
    db = FactsSession([])
    assert await facts_candidate_inputs(db, uuid.uuid4()) is None


@pytest.mark.asyncio
async def test_resume_content_uses_only_confirmed_facts():
    user_id = uuid.uuid4()
    facts = _facts(user_id) + [
        _fact(user_id, "employment", {"employer": "Ghost Corp", "title": "CTO"}, confirmed=False),
        _fact(user_id, "skill", {"name": "Fabricated"}, prohibited=True),
    ]
    db = FactsSession(facts)
    content, project_facts = await build_resume_content_from_facts(db, user_id)
    assert content is not None
    employers = [e["company"] for e in content["experience"]]
    assert employers == ["Acme"]
    all_skills = [s for cat in content["skills"] for s in cat["skills"]]
    assert "Fabricated" not in all_skills
    assert content["projects"][0]["evidence_fact_id"]
    assert project_facts and project_facts[0]["name"] == "JobPilot"


@pytest.mark.asyncio
async def test_build_candidate_profile_prefers_facts_when_flag_on(monkeypatch):
    from app.jobs.scoring.service import build_candidate_profile_with_source

    monkeypatch.setattr(settings, "feature_candidate_intelligence", True)
    user_id = uuid.uuid4()
    user = User(id=user_id, oauth_provider="dev", oauth_id="x", email="u@x.com", skills_keywords=["legacy-skill"])

    class Session(FactsSession):
        async def get(self, *a, **kw):
            return None

    db = Session(_facts(user_id))
    profile, source = await build_candidate_profile_with_source(db, user, None)
    assert source == "facts"
    assert "Python" in profile.skills
    assert profile.work_authorization == "permanent_resident"


@pytest.mark.asyncio
async def test_build_candidate_profile_falls_back_to_legacy_without_facts(monkeypatch):
    from app.jobs.scoring.service import build_candidate_profile_with_source

    monkeypatch.setattr(settings, "feature_candidate_intelligence", True)
    user_id = uuid.uuid4()
    user = User(id=user_id, oauth_provider="dev", oauth_id="x", email="u@x.com", skills_keywords=["legacy-skill"])

    class Session(FactsSession):
        async def get(self, *a, **kw):
            return None

    db = Session([])  # no facts; legacy profile query also returns empty
    profile, source = await build_candidate_profile_with_source(db, user, None)
    assert source == "legacy"
    assert profile is not None and "legacy-skill" in profile.skills
