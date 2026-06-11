import json

from app.agents.editor_agent import (
    apply_change,
    coerce_change_value,
    format_path_label,
    serialize_diff_value,
)


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


def test_apply_change_updates_skills_list(sample_resume):
    new_skills = ["Python", "Go", "Rust"]
    updated = apply_change(sample_resume, "skills[0].skills", new_skills)
    assert updated["skills"][0]["skills"] == new_skills


def test_apply_change_parses_json_list_string(sample_resume):
    payload = '["Python", "TypeScript", "SQL"]'
    updated = apply_change(sample_resume, "skills[0].skills", payload)
    assert updated["skills"][0]["skills"] == ["Python", "TypeScript", "SQL"]


def test_coerce_change_value_parses_json():
    assert coerce_change_value('["a", "b"]') == ["a", "b"]
    assert coerce_change_value("plain text") == "plain text"


def test_serialize_diff_value_preserves_lists():
    assert serialize_diff_value(["Python", "Go"]) == json.dumps(["Python", "Go"])


def test_format_path_label_summary(sample_resume):
    assert format_path_label(sample_resume, "summary") == "Summary"


def test_format_path_label_contact_field(sample_resume):
    assert format_path_label(sample_resume, "contact.email") == "Contact · Email"


def test_format_path_label_experience_bullet(sample_resume):
    label = format_path_label(sample_resume, "experience[0].bullets[1]")
    assert "Experience · Acme Corp" in label
    assert "Bullet 2" in label
