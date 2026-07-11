from app.models.job_intelligence import INBOX_STATUSES, InboxJob


def test_inbox_status_constraint_matches_constant_exactly():
    """Verify the CheckConstraint text is derived from INBOX_STATUSES constant."""
    constraint = next(
        c for c in InboxJob.__table__.constraints
        if getattr(c, "name", None) == "ck_inbox_jobs_status"
    )
    text = str(constraint.sqltext)
    for status in INBOX_STATUSES:
        assert f"'{status}'" in text, f"Status '{status}' not found in constraint"
    # no extra values snuck into the constraint that aren't in the constant
    expected_quotes = len(INBOX_STATUSES) * 2
    actual_quotes = text.count("'")
    assert actual_quotes == expected_quotes, \
        f"Expected {expected_quotes} quotes, got {actual_quotes}"
