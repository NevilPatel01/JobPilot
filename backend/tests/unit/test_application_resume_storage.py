"""Unit tests for application resume filesystem storage."""

from uuid import uuid4

from app.services.application_resume_storage import (
    delete_uploaded_resume,
    read_uploaded_resume,
    resume_path_for,
    save_uploaded_resume,
)


def test_save_read_delete_uploaded_resume(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "app.services.application_resume_storage.settings.application_uploads_dir",
        str(tmp_path),
    )
    user_id = uuid4()
    app_id = uuid4()
    payload = b"%PDF-1.4 fake"

    path = save_uploaded_resume(user_id, app_id, payload)
    assert path == resume_path_for(user_id, app_id)
    assert path.is_file()
    assert read_uploaded_resume(user_id, app_id) == payload
    assert delete_uploaded_resume(user_id, app_id) is True
    assert read_uploaded_resume(user_id, app_id) is None
    assert delete_uploaded_resume(user_id, app_id) is False
