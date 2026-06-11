from app.agents.editor_agent import apply_change


def test_apply_change_updates_summary(sample_resume):
    updated = apply_change(sample_resume, "summary", "New summary text")
    assert updated["summary"] == "New summary text"
    assert sample_resume["summary"] != "New summary text"


def test_apply_change_updates_nested_bullet(sample_resume):
    updated = apply_change(sample_resume, "experience[0].bullets[0]", "Improved bullet with 40% latency reduction.")
    assert updated["experience"][0]["bullets"][0] == "Improved bullet with 40% latency reduction."


def test_apply_change_updates_contact_field(sample_resume):
    updated = apply_change(sample_resume, "contact.email", "new@example.com")
    assert updated["contact"]["email"] == "new@example.com"
