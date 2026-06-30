from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.pipeline_helpers import PipelineState, emit, run_step


async def score_ats(state: PipelineState, db: AsyncSession) -> PipelineState:
    from app.services.ats.scorer import score_resume

    resume_id = state["resume_id"]
    await emit(resume_id, "agent_step", {"step": "ats_score", "status": "running"})

    result = score_resume(
        state.get("content") or {},
        state.get("job_description", ""),
        state.get("jd_analysis") or {},
    )
    state["ats_result"] = result.to_dict()

    await run_step(db, resume_id, "ats_score", "completed", state["ats_result"])
    await emit(resume_id, "agent_step", {"step": "ats_score", "status": "completed", "data": state["ats_result"]})
    return state
