from fastapi import APIRouter

from app.api.routes.resumes.crud import router as _crud_router
from app.api.routes.resumes.editor import router as _editor_router
from app.api.routes.resumes.pipeline import router as _pipeline_router

router = APIRouter()
router.include_router(_crud_router)
router.include_router(_editor_router)
router.include_router(_pipeline_router)

# Re-export helpers used by documents_api and cover_letters routes
from app.api.routes.resumes._helpers import (  # noqa: E402
    _ats_response,
    _chat_message_response,
    _ensure_not_processing,
    _get_resume,
    _get_structured_profile,
    _pipeline_task,
    _require_llm_config,
    _resume_response,
    _resume_response_with_status,
)

# Re-export route handlers used by documents_api
from app.api.routes.resumes.crud import export_pdf  # noqa: E402
from app.api.routes.resumes.editor import chat_edit  # noqa: E402
from app.api.routes.resumes.pipeline import run_ats_score  # noqa: E402

__all__ = [
    "router",
    "_ats_response",
    "_chat_message_response",
    "_ensure_not_processing",
    "_get_resume",
    "_get_structured_profile",
    "_pipeline_task",
    "_require_llm_config",
    "_resume_response",
    "_resume_response_with_status",
    "export_pdf",
    "chat_edit",
    "run_ats_score",
]
