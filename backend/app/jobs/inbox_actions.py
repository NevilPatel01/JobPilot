from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import UserApplication
from app.models.job_intelligence import InboxJob
from app.models.resume import ResumeDocument
from app.models.user import User


async def mark_inbox_applied(
    session: AsyncSession,
    inbox_job: InboxJob,
    user: User,
) -> UserApplication:
    application = await session.get(UserApplication, inbox_job.application_id) if inbox_job.application_id else None
    if not application:
        salary = None
        if inbox_job.job.salary_min or inbox_job.job.salary_max:
            salary = (
                f"${inbox_job.job.salary_min or '?'}-${inbox_job.job.salary_max or '?'} "
                f"{inbox_job.job.salary_currency}"
            )
        application = UserApplication(
            user_id=user.id,
            job_id=inbox_job.job_id,
            status="applied",
            job_title=inbox_job.job.title,
            company=inbox_job.job.company,
            job_url=inbox_job.job.apply_url or inbox_job.job.url,
            salary_range=salary,
            date_applied=date.today(),
        )
        session.add(application)
        await session.flush()
        inbox_job.application_id = application.id
    else:
        application.status = "applied"
        application.date_applied = application.date_applied or date.today()

    inbox_job.status = "applied"
    inbox_job.tracker_summary = "Applied"
    if inbox_job.resume_id:
        resume = await session.get(ResumeDocument, inbox_job.resume_id)
        if resume:
            resume.application_id = application.id
    return application
