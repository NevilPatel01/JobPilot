import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.json_utils import extract_json_object
from app.agents.pipeline_helpers import PipelineState, emit, run_step
from app.agents.retry import invoke_llm
from app.agents.validation import guard_tailored_content
from app.schemas.resume_content import ResumeContent
from app.services.llm.client import create_chat_model, get_user_llm_config
from app.services.rag.ingest import search_chunks

logger = logging.getLogger(__name__)

_TAILOR_INSIGHTS = [
    "Aligned experience bullets with the job requirements",
    "Wove ATS keywords into bullets, summary, and skills",
    "Optimized the summary and skills for the target role",
]

_COMMON_RULES = """GROUND TRUTH — never violate:
- Keep every employer, company, job title, institution, degree, project name, and DATE exactly as written.
- Never invent numeric metrics. Keep existing numbers; do not add new percentages, dollar amounts, or counts.
- Do not remove experience entries, education, or projects. Do not drop bullets unless merging duplicates.
- Preserve the candidate's real career — only the WORDING and emphasis change, plus added skills/keywords."""

_SYSTEM = "You are an expert technical resume writer and ATS optimizer. Return ONLY a raw JSON object matching the input schema — no markdown, no prose."


def _tailor_prompt(content: ResumeContent, jd_analysis: dict, *, job_title: str, company: str, rag: str, aggressive: bool) -> str:
    keywords = ", ".join(str(k) for k in (jd_analysis.get("keywords") or [])[:30])
    required = ", ".join(str(s) for s in (jd_analysis.get("required_skills") or [])[:25])

    if aggressive:
        strategy = f"""AGGRESSIVE MODE — maximize ATS match for the role "{job_title or 'the target role'}":
- Rewrite EVERY experience and project bullet to mirror the job description's language; lead each with a strong action verb and a relevant JD keyword.
- Add the JD's required skills and tools that are standard for this role and consistent with the candidate's background, grouped into clear skill categories. Do NOT add tools the candidate clearly never used, and NEVER invent employers, titles, dates, or numbers.
- Ensure every ATS keyword below appears at least once somewhere in the resume where it is truthful.
- Rewrite the summary as a 2-3 line pitch for this exact role using the candidate's real experience."""
    else:
        strategy = """STANDARD MODE — meaningful, truthful optimization:
- Reword bullets to naturally include the JD keywords and required skills the candidate has clearly demonstrated.
- You MAY add skills the candidate's experience clearly implies (e.g. "REST APIs" if bullets describe building APIs), even if not explicitly listed. Do not add unrelated tools.
- Reorder bullets so the most job-relevant ones come first. Rewrite the summary to address the role's core requirements."""

    return f"""Tailor this resume for the target job so it passes ATS keyword screening while staying truthful.

{_COMMON_RULES}

{strategy}

ATS KEYWORDS TO INCORPORATE (truthfully): {keywords or "(infer from JD analysis)"}
REQUIRED SKILLS TO SURFACE: {required or "(infer from JD analysis)"}

Target title: {job_title or ""}
Company context: {company}

Current resume JSON:
{content.model_dump_json()}

JD analysis: {json.dumps(jd_analysis)}
Supporting evidence from the candidate's history (RAG): {rag[:3000]}"""


async def _run_tailor(state: PipelineState, db: AsyncSession, prompt: str, source_content: dict) -> tuple[dict, list[str]]:
    llm_config = await get_user_llm_config(db, state["user_id"])
    llm = create_chat_model(llm_config)
    res = await invoke_llm(llm, [SystemMessage(content=_SYSTEM), HumanMessage(content=prompt)])
    raw = res.content if isinstance(res.content, str) else str(res.content)
    tailored = extract_json_object(raw)
    validated = ResumeContent.model_validate(tailored).model_dump()
    return guard_tailored_content(source_content, validated)


async def tailor_resume(state: PipelineState, db: AsyncSession) -> PipelineState:
    resume_id = state["resume_id"]
    await emit(resume_id, "agent_step", {"step": "tailor_resume", "status": "running"})
    llm_config = await get_user_llm_config(db, state["user_id"])
    source_content = state.get("source_content") or state.get("content") or {}
    content = ResumeContent.model_validate(source_content)

    if not llm_config:
        state["content"] = content.model_dump()
        state["tailoring_insights"] = ["No API key configured — using profile as-is."]
        await run_step(db, resume_id, "tailor_resume", "completed")
        await emit(resume_id, "agent_step", {"step": "tailor_resume", "status": "completed"})
        return state

    chunks = await search_chunks(db, state["user_id"], state.get("job_description", ""), llm_config)
    rag_context = "\n---\n".join(c.chunk_text for c in chunks[:6])
    jd_analysis = state.get("jd_analysis") or {}
    company = state.get("company_research", {}).get("summary", "")
    prompt = _tailor_prompt(
        content,
        jd_analysis,
        job_title=state.get("job_title") or state.get("company_name") or "",
        company=company,
        rag=rag_context,
        aggressive=bool(state.get("aggressive")),
    )

    try:
        cleaned, guard_warnings = await _run_tailor(state, db, prompt, source_content)
        state["content"] = cleaned
        state["tailoring_insights"] = _TAILOR_INSIGHTS + guard_warnings
    except Exception as e:
        logger.warning("Resume tailoring failed: %s", e)
        state["content"] = content.model_dump()
        state["tailoring_insights"] = [f"Tailoring skipped: {e}"]

    await run_step(db, resume_id, "tailor_resume", "completed")
    await emit(resume_id, "agent_step", {"step": "tailor_resume", "status": "completed"})
    return state


async def refine_for_ats(state: PipelineState, db: AsyncSession, ats_result: dict) -> dict:
    """One score-guided improvement pass: weave in the missing keywords the ATS
    scorer flagged, then return guarded content. Raises on failure so the caller
    can stop the loop."""
    source_content = state.get("source_content") or {}
    current = ResumeContent.model_validate(state.get("content") or source_content)
    missing = ", ".join(str(k) for k in (ats_result.get("missing_keywords") or [])[:25])
    jd_analysis = state.get("jd_analysis") or {}

    prompt = f"""This resume scored {ats_result.get('overall_score')}/100 on ATS for the role "{state.get('job_title') or ''}".

{_COMMON_RULES}

Raise the score by naturally incorporating these MISSING keywords wherever they are truthful for this candidate
(rework existing bullets, the summary, and the skills section). You MAY add skills the candidate's experience implies.

MISSING KEYWORDS (add truthfully): {missing or "(none flagged — strengthen alignment with the JD)"}
JD analysis: {json.dumps(jd_analysis)}

Current resume JSON:
{current.model_dump_json()}"""

    cleaned, _ = await _run_tailor(state, db, prompt, source_content)
    return cleaned
