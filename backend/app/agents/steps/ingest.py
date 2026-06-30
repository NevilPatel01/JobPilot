from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.pipeline_helpers import PipelineState, emit, run_step
from app.services.llm.client import get_user_llm_config
from app.services.rag.ingest import ingest_resume_content, ingest_text


async def ingest_context(state: PipelineState, db: AsyncSession) -> PipelineState:
    resume_id = state["resume_id"]
    await emit(resume_id, "agent_step", {"step": "ingest_context", "status": "running"})
    llm_config = await get_user_llm_config(db, state["user_id"])

    if llm_config and state.get("job_description"):
        await ingest_text(db, state["user_id"], "job_description", resume_id, state["job_description"], llm_config)

    if llm_config and state.get("source_type") == "upload" and state.get("source_content"):
        await ingest_resume_content(
            db,
            state["user_id"],
            state["source_content"],
            llm_config,
            source_id=resume_id,
        )

    await run_step(db, resume_id, "ingest_context", "completed")
    await emit(resume_id, "agent_step", {"step": "ingest_context", "status": "completed"})
    return state
