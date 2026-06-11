"""Rule-based suggestion item tests."""

from app.services.ats.scorer import score_resume
from app.services.ats.suggestions import build_rule_based_items


def test_build_rule_based_items_includes_keyword_prompt(sample_resume, sample_jd, sample_jd_analysis):
    result = score_resume(sample_resume, sample_jd, sample_jd_analysis)
    items = build_rule_based_items(result)
    assert items
    assert all("text" in i and "prompt" in i and "priority" in i and "category" in i for i in items)
    keyword_items = [i for i in items if i["category"] == "keyword"]
    if result.missing_keywords:
        assert keyword_items
        assert "incorporate" in keyword_items[0]["prompt"].lower() or "keywords" in keyword_items[0]["prompt"].lower()


def test_build_rule_based_items_caps_length(sample_resume, sample_jd):
    jd_analysis = {
        "required_skills": [f"Skill{i}" for i in range(20)],
        "keywords": [f"Keyword{i}" for i in range(20)],
    }
    result = score_resume(sample_resume, sample_jd, jd_analysis)
    items = build_rule_based_items(result)
    assert len(items) <= 8
