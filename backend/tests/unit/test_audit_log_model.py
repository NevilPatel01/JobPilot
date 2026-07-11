from app.models.audit import AuditLog
from app.models.application import USER_APPLICATION_STATUSES, UserApplication


def test_audit_log_has_provenance_columns():
    cols = {c.name for c in AuditLog.__table__.columns}
    assert {"user_id", "action", "entity_type", "entity_id", "model_name", "prompt_version", "confidence"}.issubset(cols)


def test_audit_log_entity_id_is_string_not_fk():
    col = AuditLog.__table__.columns["entity_id"]
    assert not col.foreign_keys  # deliberately polymorphic, see plan Task 1 rationale


def test_user_application_status_constraint_matches_constant():
    constraint = next(
        c for c in UserApplication.__table__.constraints
        if getattr(c, "name", None) == "ck_user_applications_status"
    )
    for status in USER_APPLICATION_STATUSES:
        assert f"'{status}'" in str(constraint.sqltext)
