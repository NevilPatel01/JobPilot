import uuid
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.api.routes.extension import _capture_response, build_capture_job
from app.api.schemas import ExtensionCaptureRequest
from app.core.api_auth import get_user_from_api_token
from app.models.job_intelligence import CapturedJob
from app.services.location import is_canadian_job


def capture_request(**overrides) -> ExtensionCaptureRequest:
    data = {
        "title": "Application Support Analyst",
        "company": "Example Financial",
        "url": "https://jobs.example.com/application-support?utm_source=linkedin",
        "location": "Toronto, Ontario, Canada",
        "description": "Support Canadian production systems using SQL and ServiceNow.",
        "skills": ["SQL", "ServiceNow"],
        "source_site": "linkedin",
        "action": "inbox",
    }
    data.update(overrides)
    return ExtensionCaptureRequest.model_validate(data)


def test_extension_payload_normalizes_through_shared_pipeline_contract() -> None:
    job = build_capture_job(capture_request())

    assert job.source == "extension"
    assert job.province == "ON"
    assert job.skills == ["SQL", "ServiceNow"]
    assert "utm_source" not in job.canonical_url


def test_selected_text_is_description_fallback() -> None:
    job = build_capture_job(capture_request(description="", selected_text="Canada role selected from page"))

    assert job.description == "Canada role selected from page"


def test_extension_capture_validates_required_url_and_action() -> None:
    with pytest.raises(ValidationError):
        capture_request(url="not a URL")
    with pytest.raises(ValidationError):
        capture_request(action="delete")


def test_canada_eligibility_rejects_non_canadian_capture() -> None:
    body = capture_request(location="New York, NY", description="US only role")

    assert is_canadian_job(body.location, body.description, body.title) is False


@pytest.mark.asyncio
async def test_extension_auth_requires_api_key() -> None:
    with pytest.raises(HTTPException) as exc:
        await get_user_from_api_token(None, None)  # type: ignore[arg-type]

    assert exc.value.status_code == 401


def test_duplicate_capture_response_returns_existing_inbox_state() -> None:
    capture = SimpleNamespace(id=uuid.uuid4())
    fit = SimpleNamespace(score=82, label="recommended", recommended_category="app_support_analyst")
    inbox = SimpleNamespace(
        id=uuid.uuid4(),
        job_id=uuid.uuid4(),
        status="shortlisted",
        fit_score=fit,
        ai_recommended_category="app_support_analyst",
        application_id=None,
    )

    response = _capture_response(capture, inbox, duplicate=True)  # type: ignore[arg-type]

    assert response.duplicate is True
    assert response.fit_score == 82
    assert response.inbox_job_id == inbox.id


def test_capture_audit_model_links_job_and_inbox() -> None:
    assert {fk.target_fullname for fk in CapturedJob.__table__.c.job_id.foreign_keys} == {"jobs.id"}
    assert {fk.target_fullname for fk in CapturedJob.__table__.c.inbox_job_id.foreign_keys} == {"inbox_jobs.id"}
