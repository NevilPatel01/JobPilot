from app.agents.cover_letter_agent import apply_change


def test_apply_change_updates_paragraph():
    content = {"paragraphs": ["Old text", "Keep me"], "closing": "Sincerely,"}
    updated = apply_change(content, "paragraphs[0]", "New opening paragraph.")
    assert updated["paragraphs"][0] == "New opening paragraph."
    assert updated["paragraphs"][1] == "Keep me"


def test_apply_change_updates_salutation():
    content = {"salutation": "Dear Hiring Manager,", "paragraphs": []}
    updated = apply_change(content, "salutation", "Dear Jane Smith,")
    assert updated["salutation"] == "Dear Jane Smith,"
