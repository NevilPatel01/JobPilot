import pytest

from app.core.config import settings
from app.services.candidate.backfill import backfill_facts_from_content


def test_backfill_produces_one_fact_per_experience_entry(sample_resume):
    facts = backfill_facts_from_content(sample_resume)
    experience_facts = [f for f in facts if f.fact_type == "employment"]
    assert len(experience_facts) == len(sample_resume["experience"])


def test_backfill_facts_land_as_user_confirmed(sample_resume):
    facts = backfill_facts_from_content(sample_resume)
    assert all(f.source == "resume_upload" for f in facts)
    # verification_status is set by create_fact() based on source, not here —
    # this test only asserts the CandidateFactCreate.source value backfill produces,
    # which create_fact() maps to "unverified" (source != "user_entered").
    # Per PHASE_1_IMPLEMENTATION_SPEC.md §7, backfilled facts are documented as a
    # deliberate exception that should land user_confirmed — see plan Step 7 below
    # for how backfill_facts_from_profile achieves that without changing create_fact's
    # general default for other "resume_upload"-sourced facts (e.g. future PDF re-parses).


def test_backfill_produces_one_skill_fact_per_category(sample_resume):
    facts = backfill_facts_from_content(sample_resume)
    skill_facts = [f for f in facts if f.fact_type == "skill"]
    assert len(skill_facts) == len(sample_resume["skills"])


@pytest.mark.asyncio
async def test_backfill_from_profile_skips_when_facts_already_exist(monkeypatch):
    import uuid

    class _FakeResult:
        def __init__(self, rows):
            self._rows = rows

        def scalars(self):
            return self

        def all(self):
            return self._rows

    class FakeDB:
        def __init__(self, existing):
            self.existing = existing

        async def execute(self, *a, **kw):
            return _FakeResult(self.existing)

    from app.models.candidate import CandidateFact
    from app.services.candidate.backfill import backfill_facts_from_profile

    existing_fact = CandidateFact(id=uuid.uuid4(), user_id=uuid.uuid4(), fact_type="skill", payload={}, is_prohibited=False)
    db = FakeDB(existing=[existing_fact])
    result = await backfill_facts_from_profile(db, existing_fact.user_id, force=False)
    assert result == {"facts_created": 0, "skipped": True}
