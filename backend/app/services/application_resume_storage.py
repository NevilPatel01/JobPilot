"""Filesystem storage for PDFs uploaded onto tracker applications."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

from app.core.config import settings

# backend/ — parent of app/
_BACKEND_ROOT = Path(__file__).resolve().parents[2]


def uploads_root() -> Path:
    configured = Path(settings.application_uploads_dir)
    root = configured if configured.is_absolute() else _BACKEND_ROOT / configured
    root.mkdir(parents=True, exist_ok=True)
    return root


def resume_path_for(user_id: UUID, application_id: UUID) -> Path:
    user_dir = uploads_root() / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir / f"{application_id}.pdf"


def save_uploaded_resume(user_id: UUID, application_id: UUID, data: bytes) -> Path:
    path = resume_path_for(user_id, application_id)
    path.write_bytes(data)
    return path


def read_uploaded_resume(user_id: UUID, application_id: UUID) -> bytes | None:
    path = resume_path_for(user_id, application_id)
    if not path.is_file():
        return None
    return path.read_bytes()


def delete_uploaded_resume(user_id: UUID, application_id: UUID) -> bool:
    path = resume_path_for(user_id, application_id)
    if path.is_file():
        path.unlink()
        return True
    return False
