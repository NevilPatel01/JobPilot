from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.schemas import ExtensionCaptureRequest, ExtensionCaptureResponse, ExtensionInboxActionRequest
from app.core.api_auth import get_user_from_api_token
from app.core.config import settings
from app.core.database import get_db
from app.core.rate_limit import limiter
from app.jobs.inbox_actions import mark_inbox_applied
from app.jobs.pipeline.ingest import ingest_job
from app.jobs.pipeline.normalizer import normalize_job
from app.models.job_intelligence import CapturedJob, InboxJob
from app.models.user import User
from app.services.location import is_canadian_job

router = APIRouter()


def build_capture_job(body: ExtensionCaptureRequest):
    description = body.description.strip() or body.selected_text.strip()
    return normalize_job(
        {
            "title": body.title,
            "company": body.company,
            "location": body.location,
            "description": description,
            "skills": body.skills,
            "job_type": body.job_type,
            "salary_min": body.salary_min,
            "salary_max": body.salary_max,
            "currency": body.currency,
            "apply_url": str(body.url),
            "source": "extension",
            "source_job_id": None,
            "raw_payload": {
                "source_site": body.source_site,
                "selected_text": body.selected_text,
            },
        }
    )


def _capture_response(capture: CapturedJob, inbox: InboxJob, *, duplicate: bool) -> ExtensionCaptureResponse:
    fit = inbox.fit_score
    return ExtensionCaptureResponse(
        capture_id=capture.id,
        job_id=inbox.job_id,
        inbox_job_id=inbox.id,
        status=inbox.status,
        duplicate=duplicate,
        fit_score=fit.score if fit else None,
        fit_label=fit.label if fit else None,
        recommended_category=(fit.recommended_category if fit else inbox.ai_recommended_category),
        application_id=inbox.application_id,
        message=("Existing Inbox job updated" if duplicate else "Job saved to your Inbox"),
    )


async def _load_user_inbox(db: AsyncSession, inbox_id: UUID, user_id: UUID) -> InboxJob:
    result = await db.execute(
        select(InboxJob)
        .where(InboxJob.id == inbox_id, InboxJob.user_id == user_id)
        .options(selectinload(InboxJob.job), selectinload(InboxJob.fit_score))
    )
    inbox = result.scalar_one_or_none()
    if not inbox:
        raise HTTPException(status_code=404, detail="Inbox job not found")
    return inbox


@router.post("/capture", response_model=ExtensionCaptureResponse)
@limiter.limit(settings.public_api_rate_limit_create)
async def capture_job(
    request: Request,
    body: ExtensionCaptureRequest,
    user: User = Depends(get_user_from_api_token),
    db: AsyncSession = Depends(get_db),
):
    payload = body.model_dump(mode="json")
    capture = CapturedJob(
        user_id=user.id,
        source_url=str(body.url),
        source_site=body.source_site,
        action=body.action,
        raw_payload=payload,
    )
    db.add(capture)
    await db.flush()

    description = body.description or body.selected_text
    if not is_canadian_job(body.location, description, body.title):
        capture.status = "rejected"
        capture.error = "Job does not appear to be Canada-eligible"
        capture.processed_at = datetime.now(timezone.utc)
        await db.commit()
        raise HTTPException(status_code=422, detail=capture.error)

    normalized = build_capture_job(body)
    result = await ingest_job(db, normalized, user_id=user.id, captured_via="extension")
    inbox = result.inbox_job
    if not inbox:
        capture.status = "failed"
        capture.error = "Failed to create Inbox item"
        await db.commit()
        raise HTTPException(status_code=500, detail=capture.error)
    if inbox.status == "archived":
        inbox.status = "new"
    if body.action == "applied":
        await mark_inbox_applied(db, inbox, user)

    is_duplicate = result.duplicate_reason is not None or not result.created
    capture.job_id = result.job.id
    capture.inbox_job_id = inbox.id
    capture.status = "applied" if body.action == "applied" else "duplicate" if is_duplicate else "normalized"
    capture.processed_at = datetime.now(timezone.utc)
    await db.commit()
    loaded = await _load_user_inbox(db, inbox.id, user.id)
    response = _capture_response(capture, loaded, duplicate=is_duplicate)
    if body.action == "applied":
        response.message = "Job saved and added to your Tracker"
    return response


@router.patch("/inbox/{inbox_id}", response_model=ExtensionCaptureResponse)
@limiter.limit(settings.public_api_rate_limit_default)
async def update_captured_job(
    request: Request,
    inbox_id: UUID,
    body: ExtensionInboxActionRequest,
    user: User = Depends(get_user_from_api_token),
    db: AsyncSession = Depends(get_db),
):
    inbox = await _load_user_inbox(db, inbox_id, user.id)
    if body.action == "applied":
        await mark_inbox_applied(db, inbox, user)
    else:
        inbox.status = body.action
    await db.commit()
    inbox = await _load_user_inbox(db, inbox.id, user.id)
    capture_result = await db.execute(
        select(CapturedJob)
        .where(CapturedJob.user_id == user.id, CapturedJob.inbox_job_id == inbox.id)
        .order_by(CapturedJob.created_at.desc())
        .limit(1)
    )
    capture = capture_result.scalar_one_or_none()
    if not capture:
        capture = CapturedJob(
            user_id=user.id,
            job_id=inbox.job_id,
            inbox_job_id=inbox.id,
            source_url=inbox.job.url,
            source_site="extension",
            status=body.action,
            action=body.action,
            raw_payload={},
            processed_at=datetime.now(timezone.utc),
        )
        db.add(capture)
    else:
        capture.status = body.action
        capture.action = body.action
        capture.processed_at = datetime.now(timezone.utc)
    await db.commit()
    response = _capture_response(capture, inbox, duplicate=True)
    response.message = f"Job marked {body.action}"
    return response
