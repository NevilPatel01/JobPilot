import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.pipeline_helpers import PipelineState, emit, run_step
from app.agents.retry import invoke_llm
from app.agents.validation import guard_tailored_content
from app.schemas.resume_content import ResumeContent
from app.services.llm.client import create_chat_model, get_user_llm_config
from app.services.rag.ingest import search_chunks

logger = logging.getLogger(__name__)

_TAILOR_INSIGHTS = [
    "Aligned experience bullets with job requirements",
    "Incorporated ATS keywords naturally into content",
    "Optimized summary and skills for target role",
]


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

    llm = create_chat_model(llm_config)
    chunks = await search_chunks(db, state["user_id"], state.get("job_description", ""), llm_config)
    rag_context = "\n---\n".join(c.chunk_text for c in chunks[:6])
    jd_analysis = state.get("jd_analysis") or {}
    jd = json.dumps(jd_analysis)
    company = state.get("company_research", {}).get("summary", "")

    ats_keywords = ", ".join(str(k) for k in (jd_analysis.get("keywords") or [])[:25])
    required_skills = ", ".join(str(s) for s in (jd_analysis.get("required_skills") or [])[:20])

    prompt = f"""You are an expert ATS-optimized resume writer. Tailor the resume JSON for the target job.

STRICT RULES:
1. Return ONLY valid JSON matching the exact same schema as the input.
2. Preserve every factual claim, employer, job title, date, degree, project name, and metric exactly.
3. Do NOT invent skills, tools, certifications, companies, projects, or accomplishments absent from the source.
4. Naturally weave the ATS keywords below into bullets and summary (no keyword stuffing).
5. Reorder bullets within each experience entry so the most job-relevant accomplishments appear first.
6. Write the summary to directly address the role's core requirements using the candidate's real experience.
7. Use strong action verbs and preserve existing numeric metrics in bullets.

ATS KEYWORDS TO INCORPORATE NATURALLY:
{ats_keywords or "(see JD analysis)"}

REQUIRED SKILLS TO HIGHLIGHT:
{required_skills or "(see JD analysis)"}

Current resume JSON:
{content.model_dump_json()}

JD analysis: {jd}
Target title: {state.get("job_title") or ""}
Target company: {state.get("company_name") or ""}
Company context: {company}
RAG context: {rag_context[:3000]}"""

    try:
        res = await invoke_llm(
            llm,
            [
                SystemMessage(content="You are an expert resume writer. Return only JSON."),
                HumanMessage(content=prompt),
            ],
        )
        raw = res.content if isinstance(res.content, str) else str(res.content)
        tailored = json.loads(raw)
        validated = ResumeContent.model_validate(tailored).model_dump()
        cleaned, guard_warnings = guard_tailored_content(source_content, validated)
        state["content"] = cleaned
        state["tailoring_insights"] = _TAILOR_INSIGHTS + guard_warnings
    except Exception as e:
        logger.warning("Resume tailoring failed: %s", e)
        state["content"] = content.model_dump()
        state["tailoring_insights"] = [f"Tailoring skipped: {e}"]

    await run_step(db, resume_id, "tailor_resume", "completed")
    await emit(resume_id, "agent_step", {"step": "tailor_resume", "status": "completed"})
    return state
