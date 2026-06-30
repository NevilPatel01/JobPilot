"""Integration tests for the resume generation pipeline (agents/graph.py).

These drive the real `run_generation_pipeline` orchestration — real fabrication
guard, real LaTeX rendering, real ATS scoring — with the LLM, RAG, and Socket.IO
seams mocked and a lightweight in-memory fake DB session. They need no Postgres,
so they run in CI where no database service is available.

A genuine HTTP + Tectonic + real-LLM end-to-end run is covered separately (manual
verification / the verify-resume-pipeline skill).
"""

import json
import types
from copy import deepcopy
from uuid import uuid4

import pytest

from app.agents import graph
from app.agents.steps import analyze as analyze_step
from app.agents.steps import cover_letter as cover_letter_step
from app.agents.steps import ingest as ingest_step
from app.agents.steps import tailor as tailor_step
from app.models.resume import AgentRun
from app.services.resume.pdf_compiler import compile_latex_to_pdf_with_status
from app.services.resume.renderer import render_resume_latex
from app.sockets.chat import sio


# --------------------------------------------------------------------------- #
# Fakes / helpers
# --------------------------------------------------------------------------- #
class _FakeResult:
    def scalar_one_or_none(self):
        return None

    def scalars(self):
        return self

    def all(self):
        return []

    def first(self):
        return None


class FakeSession:
    """Minimal async SQLAlchemy session stand-in for orchestration tests."""

    def __init__(self):
        self.added: list = []

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        pass

    async def flush(self):
        pass

    async def refresh(self, obj):
        pass

    async def delete(self, obj):
        pass

    async def get(self, model, ident):
        return None

    async def execute(self, *args, **kwargs):
        return _FakeResult()


def _msg(content: str):
    return types.SimpleNamespace(content=content)


def _make_resume(sample_resume: dict, *, create_cover_letter: bool = True, company_url=None):
    """A ResumeDocument-shaped object the pipeline can read and mutate."""
    return types.SimpleNamespace(
        id=uuid4(),
        user_id=uuid4(),
        title="Senior Backend Engineer",
        job_description="We need a Senior Python/FastAPI engineer to build microservices.",
        company_url=company_url,
        company_name="TargetCo",
        create_cover_letter=create_cover_letter,
        cover_letter_meta={"hiring_manager_name": "Pat Lee"},
        content_json=deepcopy(sample_resume),
        source_type="profile",
        insights_json={},
        inbox_job_id=None,
        status="processing",
        latex_source="",
    )


def _agent_run_order(session: FakeSession) -> list[str]:
    return [obj.agent_type for obj in session.added if isinstance(obj, AgentRun)]


@pytest.fixture
def patched_pipeline(monkeypatch, sample_resume):
    """Patch every external seam: Socket.IO, LLM, RAG, ATS persistence.

    Returns the canned tailored content (which injects a fabricated employer so
    the validation guard has something to strip) and an ats-save spy.
    """

    async def _noop(*args, **kwargs):
        return None

    # Socket.IO — never touch a real server.
    monkeypatch.setattr(sio, "emit", _noop)

    dummy_config = object()

    async def _get_cfg(*args, **kwargs):
        return dummy_config

    def _chat_model(*args, **kwargs):
        return object()

    # ingest step
    monkeypatch.setattr(ingest_step, "get_user_llm_config", _get_cfg)
    monkeypatch.setattr(ingest_step, "ingest_text", _noop)
    monkeypatch.setattr(ingest_step, "ingest_resume_content", _noop)

    # analyze step
    jd_analysis = {
        "required_skills": ["Python", "FastAPI", "PostgreSQL"],
        "keywords": ["Python", "FastAPI", "REST API", "async"],
        "responsibilities": ["Build backend services"],
        "seniority": "Senior",
    }

    async def _analyze_llm(*args, **kwargs):
        return _msg(json.dumps(jd_analysis))

    monkeypatch.setattr(analyze_step, "get_user_llm_config", _get_cfg)
    monkeypatch.setattr(analyze_step, "create_chat_model", _chat_model)
    monkeypatch.setattr(analyze_step, "invoke_llm", _analyze_llm)

    # tailor step — inject a fabricated employer that the guard must remove.
    tailored = deepcopy(sample_resume)
    tailored["summary"] = "Senior Python/FastAPI engineer building scalable REST microservices."
    tailored["experience"].append(
        {
            "id": "fake1",
            "company": "FakeCorp Industries",
            "title": "Principal Engineer",
            "location": "Remote",
            "start_date": "2010",
            "end_date": "2012",
            "bullets": ["Invented an accomplishment that is not in the source profile."],
        }
    )

    async def _tailor_llm(*args, **kwargs):
        return _msg(json.dumps(tailored))

    async def _search_chunks(*args, **kwargs):
        return []

    monkeypatch.setattr(tailor_step, "get_user_llm_config", _get_cfg)
    monkeypatch.setattr(tailor_step, "create_chat_model", _chat_model)
    monkeypatch.setattr(tailor_step, "invoke_llm", _tailor_llm)
    monkeypatch.setattr(tailor_step, "search_chunks", _search_chunks)

    # cover letter step
    async def _cover_llm(*args, **kwargs):
        return _msg(json.dumps({"paragraphs": ["Para one.", "Para two."], "closing": "Sincerely,"}))

    monkeypatch.setattr(cover_letter_step, "get_user_llm_config", _get_cfg)
    monkeypatch.setattr(cover_letter_step, "create_chat_model", _chat_model)
    monkeypatch.setattr(cover_letter_step, "invoke_llm", _cover_llm)

    # ATS persistence — record the call instead of hitting a DB.
    ats_calls: list = []

    async def _save_ats(db, resume, user_id, enrich_llm=False):
        ats_calls.append({"resume": resume, "enrich_llm": enrich_llm})

    monkeypatch.setattr(graph, "save_ats_score", _save_ats)

    return types.SimpleNamespace(jd_analysis=jd_analysis, tailored=tailored, ats_calls=ats_calls)


# --------------------------------------------------------------------------- #
# Tests
# --------------------------------------------------------------------------- #
async def test_full_pipeline_runs_all_steps_in_order(patched_pipeline, sample_resume):
    db = FakeSession()
    resume = _make_resume(sample_resume, create_cover_letter=True)

    await graph.run_generation_pipeline(db, resume, mode="full")

    assert resume.status == "completed"
    assert _agent_run_order(db) == [
        "ingest_context",
        "analyze_jd",
        "research_company",
        "tailor_resume",
        "cover_letter",
        "ats_score",
    ]


async def test_full_pipeline_persists_content_latex_ats_and_cover_letter(patched_pipeline, sample_resume):
    db = FakeSession()
    resume = _make_resume(sample_resume, create_cover_letter=True)

    await graph.run_generation_pipeline(db, resume, mode="full")

    # content_json was updated from the tailored output
    assert resume.content_json["summary"].startswith("Senior Python/FastAPI engineer")
    # latex_source was rendered and reflects the candidate
    assert resume.latex_source
    assert "Jane Developer" in resume.latex_source
    # insights captured the JD analysis
    assert resume.insights_json["jd_analysis"]["seniority"] == "Senior"
    assert resume.insights_json["last_step"] == "completed"
    # ATS score persistence was invoked
    assert len(patched_pipeline.ats_calls) == 1
    assert patched_pipeline.ats_calls[0]["enrich_llm"] is True
    # a cover letter document was created
    from app.models.cover_letter import CoverLetterDocument

    assert any(isinstance(o, CoverLetterDocument) for o in db.added)


async def test_validation_guard_strips_fabricated_employer(patched_pipeline, sample_resume):
    db = FakeSession()
    resume = _make_resume(sample_resume, create_cover_letter=False)

    await graph.run_generation_pipeline(db, resume, mode="full")

    companies = {exp["company"] for exp in resume.content_json["experience"]}
    assert "Acme Corp" in companies
    assert "FakeCorp Industries" not in companies  # guard removed the invented employer
    insights = resume.insights_json["tailoring_insights"]
    assert any("Fact-check applied" in w for w in insights)


async def test_tailor_only_mode_skips_analysis_and_research(patched_pipeline, sample_resume):
    db = FakeSession()
    resume = _make_resume(sample_resume, create_cover_letter=False)

    await graph.run_generation_pipeline(db, resume, mode="tailor_only")

    assert resume.status == "completed"
    assert _agent_run_order(db) == ["tailor_resume", "ats_score"]


async def test_pipeline_records_failure(monkeypatch, patched_pipeline, sample_resume):
    db = FakeSession()
    resume = _make_resume(sample_resume, create_cover_letter=False)

    def _boom(*args, **kwargs):
        raise RuntimeError("latex render exploded")

    monkeypatch.setattr(graph, "render_resume_latex", _boom)

    await graph.run_generation_pipeline(db, resume, mode="full")

    assert resume.status == "failed"
    assert "latex render exploded" in resume.insights_json["pipeline_error"]
    assert any(isinstance(o, AgentRun) and o.status == "failed" for o in db.added)


def test_smoke_json_to_latex_to_pdf(sample_resume):
    """End-to-end render path: ResumeContent JSON -> LaTeX -> PDF bytes."""
    latex = render_resume_latex(sample_resume)
    assert r"\section" in latex
    pdf_bytes, used_fallback = compile_latex_to_pdf_with_status(latex)
    assert pdf_bytes.startswith(b"%PDF")
    assert isinstance(used_fallback, bool)
