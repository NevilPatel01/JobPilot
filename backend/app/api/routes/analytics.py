from collections import Counter
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import AnalyticsSummary
from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.application import UserApplication
from app.models.job import Job
from app.models.user import User
from app.services.job_filters import apply_canada_filter

router = APIRouter()


@router.get("/summary", response_model=AnalyticsSummary)
async def analytics_summary(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    apps_result = await db.execute(select(UserApplication).where(UserApplication.user_id == user.id))
    apps = apps_result.scalars().all()

    total_tracked = len(apps)
    applied_statuses = {"applied", "interviewing", "offer", "rejected"}
    applied = [a for a in apps if a.status in applied_statuses]
    interviewing = [a for a in apps if a.status in ("interviewing", "offer")]
    interview_rate = round(len(interviewing) / max(len(applied), 1) * 100, 1)

    active_jobs = (
        await db.execute(apply_canada_filter(select(func.count(Job.id)).where(Job.is_active == True)))  # noqa: E712
    ).scalar() or 0

    status_breakdown: dict[str, int] = Counter(a.status for a in apps)

    company_counts: Counter = Counter(a.company for a in apps if a.company)
    top_companies = [{"company": c, "count": n} for c, n in company_counts.most_common(10)]

    source_distribution: dict[str, int] = {}
    job_ids = [a.job_id for a in apps if a.job_id]
    if job_ids:
        jobs_result = await db.execute(select(Job).where(Job.id.in_(job_ids)))
        source_distribution = dict(Counter(j.source for j in jobs_result.scalars().all()))

    now = datetime.now(timezone.utc)
    weeks = []
    for i in range(11, -1, -1):
        week_start = now - timedelta(weeks=i + 1)
        week_end = now - timedelta(weeks=i)
        count = sum(
            1
            for a in apps
            if a.status in applied_statuses
            and a.created_at
            and week_start <= a.created_at.replace(tzinfo=timezone.utc) < week_end
        )
        weeks.append({"week": week_end.strftime("%b %d"), "count": count})

    return AnalyticsSummary(
        total_tracked=total_tracked,
        total_applied=len(applied),
        interview_rate=interview_rate,
        active_jobs_in_db=active_jobs,
        applications_over_time=weeks,
        status_breakdown=dict(status_breakdown),
        top_companies=top_companies,
        source_distribution=source_distribution,
    )
