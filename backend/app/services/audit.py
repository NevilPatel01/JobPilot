from app.models.audit import AuditLog


async def record_audit_event(
    db,
    *,
    user_id,
    action: str,
    entity_type: str,
    entity_id: str,
    before: dict | None = None,
    after: dict | None = None,
    model_name: str | None = None,
    prompt_version: str | None = None,
    confidence: float | None = None,
) -> AuditLog:
    """Insert-only audit trail entry. Never call db.commit() here — the caller's
    transaction owns the commit boundary, matching the app's existing
    flush-then-caller-commits convention (see agents/pipeline_helpers.run_step)."""
    row = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        before_json=before,
        after_json=after,
        model_name=model_name,
        prompt_version=prompt_version,
        confidence=confidence,
    )
    db.add(row)
    await db.flush()
    return row
