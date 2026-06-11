from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resume import AgentRun, ResumeDocument

STALE_PROCESSING_MINUTES = 30


async def get_latest_pipeline_run(db: AsyncSession, resume_id) -> AgentRun | None:
    result = await db.execute(
        select(AgentRun)
        .where(AgentRun.resume_id == resume_id)
        .order_by(AgentRun.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_pipeline_status(db: AsyncSession, resume_id) -> tuple[str | None, str | None]:
    """Return (last_step, pipeline_error) from the most recent agent run."""
    run = await get_latest_pipeline_run(db, resume_id)
    if not run:
        return None, None
    if run.status == "failed" and run.error:
        return run.agent_type, run.error
    return run.agent_type, None


async def mark_stale_processing_resumes(db: AsyncSession, minutes: int = STALE_PROCESSING_MINUTES) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    result = await db.execute(
        select(ResumeDocument).where(
            ResumeDocument.status == "processing",
            ResumeDocument.updated_at < cutoff,
        )
    )
    stale = result.scalars().all()
    if not stale:
        return 0

    message = f"Pipeline timed out after {minutes} minutes. Use Regenerate to retry."
    for resume in stale:
        resume.status = "failed"
        insights = dict(resume.insights_json or {})
        insights["pipeline_error"] = message
        insights["last_step"] = insights.get("last_step", "processing")
        resume.insights_json = insights
        db.add(
            AgentRun(
                resume_id=resume.id,
                agent_type="pipeline",
                status="failed",
                error=message,
            )
        )
    await db.commit()
    return len(stale)
