"""Rule-based structured ATS suggestions (fallback when LLM unavailable)."""

from __future__ import annotations

from app.services.ats.scorer import ATSResult


def _priority(score: int, category: str) -> str:
    if category == "keyword" and score < 50:
        return "high"
    if score < 60:
        return "high"
    if score < 80:
        return "medium"
    return "low"


def build_rule_based_items(result: ATSResult) -> list[dict]:
    items: list[dict] = []
    missing = result.missing_keywords or []

    if missing:
        kw = ", ".join(missing[:8])
        items.append(
            {
                "text": f"Add missing keywords: {kw}",
                "prompt": f"Naturally incorporate these ATS keywords into my experience bullets and skills section: {kw}",
                "priority": _priority(result.keyword_match, "keyword"),
                "category": "keyword",
            }
        )

    if result.skills_coverage < 70 and missing:
        skills = ", ".join(missing[:6])
        items.append(
            {
                "text": f"Improve skills coverage for: {skills}",
                "prompt": f"Update my skills and relevant bullets to highlight: {skills}",
                "priority": "high" if result.skills_coverage < 50 else "medium",
                "category": "skills",
            }
        )

    if result.section_score < 80:
        items.append(
            {
                "text": "Complete all resume sections (summary, experience, education, skills, contact)",
                "prompt": "Review my resume and fill in any incomplete sections with strong, job-relevant content.",
                "priority": "medium",
                "category": "section",
            }
        )

    if result.semantic_score < 60:
        items.append(
            {
                "text": "Increase semantic alignment with the job description",
                "prompt": "Rewrite my summary and top experience bullets to mirror the job description language without keyword stuffing.",
                "priority": "medium",
                "category": "semantic",
            }
        )

    if result.formatting_score < 80:
        items.append(
            {
                "text": "Improve ATS-friendly formatting (contact info, dates, bullet structure)",
                "prompt": "Ensure contact details, employment dates, and bullet points are complete and consistently formatted for ATS parsing.",
                "priority": "low",
                "category": "formatting",
            }
        )

    for text in result.suggestions:
        if any(item["text"] == text for item in items):
            continue
        items.append(
            {
                "text": text,
                "prompt": text,
                "priority": "medium",
                "category": "general",
            }
        )

    return items[:8]
