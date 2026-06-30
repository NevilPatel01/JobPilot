import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.pipeline_helpers import PipelineState, emit, run_step
from app.agents.retry import invoke_llm
from app.services.llm.client import create_chat_model, get_user_llm_config

logger = logging.getLogger(__name__)


async def analyze_jd(state: PipelineState, db: AsyncSession) -> PipelineState:
    resume_id = state["resume_id"]
    await emit(resume_id, "agent_step", {"step": "analyze_jd", "status": "running"})
    llm_config = await get_user_llm_config(db, state["user_id"])
    jd = state.get("job_description", "")

    if not jd:
        state["jd_analysis"] = {"sections": [], "keywords": [], "required_skills": [], "warning": "No job description provided."}
    elif not llm_config:
        state["jd_analysis"] = {
            "sections": [],
            "keywords": [],
            "required_skills": [],
            "warning": "No API key — JD analysis skipped.",
        }
    else:
        llm = create_chat_model(llm_config)
        prompt = f"""Analyze this job description and return JSON with keys:
- required_skills: list of strings
- responsibilities: list of strings
- seniority: string
- keywords: list of important ATS keywords

Target title: {state.get("job_title") or ""}
Target company: {state.get("company_name") or ""}

Job Description:
{jd[:6000]}"""
        try:
            res = await invoke_llm(
                llm,
                [SystemMessage(content="Return valid JSON only."), HumanMessage(content=prompt)],
            )
            parsed = json.loads(res.content if isinstance(res.content, str) else str(res.content))
            state["jd_analysis"] = parsed
        except Exception as e:
            logger.warning("JD analysis failed: %s", e)
            state["jd_analysis"] = {"keywords": [], "required_skills": [], "responsibilities": [], "error": str(e)}

    await run_step(db, resume_id, "analyze_jd", "completed", state["jd_analysis"])
    await emit(resume_id, "agent_step", {"step": "analyze_jd", "status": "completed", "data": state["jd_analysis"]})
    return state
