import json
import logging
import re

from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.json_utils import extract_json_object
from app.agents.pipeline_helpers import PipelineState, emit, run_step
from app.agents.retry import invoke_llm
from app.agents.validation import guard_tailored_content
from app.schemas.resume_content import ProjectEntry, ResumeContent
from app.services.candidate.project_selection import classify_job_seniority, select_projects
from app.services.candidate.resume_source import project_fact_to_entry
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

_WRITING_RULES = """PROFESSIONAL WRITING STANDARDS — apply to everything you write:

SUMMARY (hard limits):
- Exactly 2-3 sentences, 60 words MAXIMUM. Cut ruthlessly — every word must earn its place.
- Sentence 1: professional identity + strongest matching qualification for THIS role. Sentence 2-3: the 2-3 most relevant proof points (real skills/domains from the candidate's history). No first person ("I"), no filler ("seeking to apply...", "passionate about"), no listing more than 4 technologies.

BULLETS (STAR/XYZ style):
- Formula: strong action verb + what was done + tool/method + real outcome. If the source bullet has a real number, keep it and make it prominent; if not, end with the qualitative result — do NOT bolt on vague outcome phrases like "ensuring scalability and reliability".
- One idea per bullet, 15-24 words, no bullet longer than 2 printed lines.
- Start every bullet with a different action verb within the same entry (Built, Designed, Led, Automated, Reduced, Shipped...). Never start with "Responsible for" or a weak verb.
- Order bullets within each entry by relevance to the target job — most relevant first.

KEYWORD DISCIPLINE (anti-stuffing):
- Each ATS keyword should appear 1-2 times across the WHOLE resume, in the bullet or skill where it is most natural. NEVER append the same phrase (e.g. "distributed systems", "production-grade") to multiple bullets — that reads as stuffing and gets resumes rejected by human reviewers.
- If a keyword doesn't fit naturally in any bullet, put it in the skills section instead of forcing it into prose.

PROJECT & EXPERIENCE RELEVANCE:
- Reorder projects so the ones most relevant to the job description come FIRST, and rewrite their bullets to emphasize the JD-relevant technology and outcomes.
- Reorder skill categories so the most JD-relevant category comes first."""

_SYSTEM = "You are an expert technical resume writer and ATS optimizer. Return ONLY a raw JSON object matching the input schema — no markdown, no prose."

_SUMMARY_MAX_WORDS = 70  # hard backstop — the prompt asks for <=60


def _enforce_summary_limit(content: dict) -> dict:
    """Backstop for when the LLM ignores the length rule: keep whole sentences
    until the word budget is spent."""
    summary = (content.get("summary") or "").strip()
    if len(summary.split()) <= _SUMMARY_MAX_WORDS:
        return content
    sentences = re.split(r"(?<=[.!?])\s+", summary)
    kept: list[str] = []
    words = 0
    for sentence in sentences:
        n = len(sentence.split())
        if kept and words + n > _SUMMARY_MAX_WORDS:
            break
        kept.append(sentence)
        words += n
    content["summary"] = " ".join(kept)
    return content


def _tailor_prompt(content: ResumeContent, jd_analysis: dict, *, job_title: str, company: str, rag: str, aggressive: bool) -> str:
    keywords = ", ".join(str(k) for k in (jd_analysis.get("keywords") or [])[:30])
    required = ", ".join(str(s) for s in (jd_analysis.get("required_skills") or [])[:25])

    if aggressive:
        strategy = f"""AGGRESSIVE MODE — maximize ATS match for the role "{job_title or 'the target role'}":
- Rewrite EVERY experience and project bullet to mirror the job description's language; lead each with a strong action verb and a relevant JD keyword.
- Add the JD's required skills and tools that are standard for this role and consistent with the candidate's background, grouped into clear skill categories. Do NOT add tools the candidate clearly never used, and NEVER invent employers, titles, dates, or numbers.
- Ensure every ATS keyword below appears at least once somewhere in the resume where it is truthful — but respect the keyword-discipline rules: prefer the skills section over repeating phrases in bullets.
- Rewrite the summary as a pitch for this exact role using the candidate's real experience."""
    else:
        strategy = """STANDARD MODE — meaningful, truthful optimization:
- Reword bullets to naturally include the JD keywords and required skills the candidate has clearly demonstrated.
- You MAY add skills the candidate's experience clearly implies (e.g. "REST APIs" if bullets describe building APIs), even if not explicitly listed. Do not add unrelated tools.
- Reorder bullets so the most job-relevant ones come first. Rewrite the summary to address the role's core requirements."""

    return f"""Tailor this resume for the target job so it passes ATS keyword screening while staying truthful, and reads like it was written by a top-tier professional resume writer.

{_COMMON_RULES}

{_WRITING_RULES}

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
    cleaned, warnings = guard_tailored_content(source_content, validated, facts_guard=state.get("facts_guard"))
    return _enforce_summary_limit(cleaned), warnings


def _apply_project_selection(state: PipelineState, content: ResumeContent, jd_analysis: dict) -> str | None:
    """Seniority-adaptive project selection for facts-based resumes.
    Deterministic rule, not LLM judgment: senior roles lean on experience,
    junior roles may show up to two relevant projects."""
    project_facts = state.get("project_facts")
    if not project_facts:
        return None
    job_title = state.get("job_title") or ""
    seniority = classify_job_seniority(job_title, jd_analysis.get("seniority"))
    job_skills = [
        str(s) for s in (jd_analysis.get("required_skills") or []) + (jd_analysis.get("keywords") or [])
    ]
    selected = select_projects(
        project_facts,
        job_skills=job_skills,
        seniority=seniority,
        experience_count=len(content.experience),
    )
    content.projects = [ProjectEntry.model_validate(project_fact_to_entry(p)) for p in selected]
    names = ", ".join(p["name"] for p in selected) or "(none — omit the projects section)"
    return (
        f"PROJECT SELECTION (deterministic, {seniority} role): include exactly these projects and no others: "
        f"{names}. Do not add, invent, or restore other projects. Only condense or reword the provided bullets."
    )


async def tailor_resume(state: PipelineState, db: AsyncSession) -> PipelineState:
    resume_id = state["resume_id"]
    await emit(resume_id, "agent_step", {"step": "tailor_resume", "status": "running"})
    llm_config = await get_user_llm_config(db, state["user_id"])
    source_content = state.get("source_content") or state.get("content") or {}
    content = ResumeContent.model_validate(source_content)
    jd_analysis = state.get("jd_analysis") or {}
    project_note = _apply_project_selection(state, content, jd_analysis)
    if project_note:
        # keep the fallback/source in sync so the guard treats the selection as ground truth
        source_content = content.model_dump()
        state["source_content"] = source_content

    if not llm_config:
        state["content"] = content.model_dump()
        state["tailoring_insights"] = ["No API key configured — using profile as-is."]
        await run_step(db, resume_id, "tailor_resume", "completed")
        await emit(resume_id, "agent_step", {"step": "tailor_resume", "status": "completed"})
        return state

    chunks = await search_chunks(db, state["user_id"], state.get("job_description", ""), llm_config)
    rag_context = "\n---\n".join(c.chunk_text for c in chunks[:6])
    company = state.get("company_research", {}).get("summary", "")
    prompt = _tailor_prompt(
        content,
        jd_analysis,
        job_title=state.get("job_title") or state.get("company_name") or "",
        company=company,
        rag=rag_context,
        aggressive=bool(state.get("aggressive")),
    )
    if project_note:
        prompt += f"\n\n{project_note}"

    try:
        cleaned, guard_warnings = await _run_tailor(state, db, prompt, source_content)
        state["content"] = cleaned
        state["tailoring_insights"] = _TAILOR_INSIGHTS + guard_warnings
    except Exception as e:
        logger.warning("Resume tailoring failed: %s", e)
        state["content"] = content.model_dump()
        state["tailoring_insights"] = [f"Tailoring skipped: {e}"]

    await run_step(db, resume_id, "tailor_resume", "completed", model_name=getattr(llm_config, "model_name", None))
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

{_WRITING_RULES}

Raise the score by incorporating these MISSING keywords wherever they are truthful for this candidate:
- FIRST CHOICE: add each missing keyword to the most fitting skills category. You MAY add skills the candidate's experience implies.
- Only rework a bullet when the keyword genuinely describes what that bullet already says — and then replace weaker wording rather than appending the keyword to the end.
- Do NOT touch bullets that already read well and contain no missing keyword. Do NOT re-add or repeat keywords the resume already contains — repetition lowers quality without raising the score.
- Keep the summary within its 60-word limit even after edits.

MISSING KEYWORDS (add truthfully): {missing or "(none flagged — strengthen alignment with the JD)"}
JD analysis: {json.dumps(jd_analysis)}

Current resume JSON:
{current.model_dump_json()}"""

    cleaned, _ = await _run_tailor(state, db, prompt, source_content)
    return cleaned
