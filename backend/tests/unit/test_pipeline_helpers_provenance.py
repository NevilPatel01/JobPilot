import pytest

from app.agents.pipeline_helpers import run_step
from app.models.resume import AgentRun


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


@pytest.mark.asyncio
async def test_run_step_without_provenance_kwargs_still_works():
    db = FakeSession()
    await run_step(db, "resume-1", "tailor_resume", "completed")
    run = db.added[0]
    assert isinstance(run, AgentRun)
    assert run.model_name is None


@pytest.mark.asyncio
async def test_run_step_with_provenance_kwargs_populates_agent_run():
    db = FakeSession()
    await run_step(
        db, "resume-1", "tailor_resume", "completed",
        model_name="claude-3-5-sonnet", prompt_version="tailor-v1", confidence=0.82,
    )
    run = db.added[0]
    assert run.model_name == "claude-3-5-sonnet"
    assert run.prompt_version == "tailor-v1"
    assert run.confidence == 0.82
