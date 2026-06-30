import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.company_summary import enrich_company_research
from app.agents.pipeline_helpers import PipelineState, emit, run_step
from app.scrapers.company_researcher import research_company
from app.services.llm.client import get_user_llm_config
from app.services.rag.ingest import ingest_text

logger = logging.getLogger(__name__)


async def research_company_step(state: PipelineState, db: AsyncSession, *, reuse: bool = False) -> PipelineState:
    resume_id = state["resume_id"]
    url = state.get("company_url")

    if reuse and state.get("company_research"):
        await emit(resume_id, "agent_step", {"step": "research_company", "status": "completed", "cached": True})
        return state

    if not url:
        state["company_research"] = {"company_name": state.get("company_name")} if state.get("company_name") else {}
        await run_step(db, resume_id, "research_company", "completed", {"skipped": True})
        await emit(resume_id, "agent_step", {"step": "research_company", "status": "completed", "skipped": True})
        return state

    await emit(resume_id, "agent_step", {"step": "research_company", "status": "running"})
    try:
        research = await research_company(url)
        llm_config = await get_user_llm_config(db, state["user_id"])
        research = await enrich_company_research(research, llm_config)
        state["company_research"] = research
        if llm_config and research.get("raw_text"):
            await ingest_text(db, state["user_id"], "company", resume_id, research["raw_text"], llm_config)
    except Exception as e:
        logger.warning("Company research failed: %s", e)
        state["company_research"] = {"error": str(e)}

    await run_step(db, resume_id, "research_company", "completed", state.get("company_research"))
    await emit(resume_id, "agent_step", {"step": "research_company", "status": "completed"})
    return state
