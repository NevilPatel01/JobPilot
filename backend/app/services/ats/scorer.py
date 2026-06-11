"""Multi-dimension ATS scoring for resume vs job description."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.schemas.resume_content import ResumeContent, resume_to_text
from app.services.match_scorer import tfidf_score, tokenize

WEIGHTS = {
    "keyword": 0.35,
    "semantic": 0.25,
    "skills": 0.20,
    "section": 0.10,
    "formatting": 0.10,
}


@dataclass
class ATSResult:
    overall_score: int
    keyword_match: int
    formatting_score: int
    semantic_score: int
    skills_coverage: int
    section_score: int
    matched_keywords: list[str] = field(default_factory=list)
    missing_keywords: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    breakdown: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "overall_score": self.overall_score,
            "keyword_match": self.keyword_match,
            "formatting_score": self.formatting_score,
            "semantic_score": self.semantic_score,
            "skills_coverage": self.skills_coverage,
            "section_score": self.section_score,
            "matched_keywords": self.matched_keywords,
            "missing_keywords": self.missing_keywords,
            "suggestions": self.suggestions,
            "breakdown": self.breakdown,
        }


def _normalize_keyword(keyword: str) -> str:
    return keyword.strip().lower()


def _keyword_in_text(keyword: str, text: str) -> bool:
    kw = _normalize_keyword(keyword)
    if not kw:
        return False
    if kw in text:
        return True
    # Multi-word: all tokens must appear
    parts = re.findall(r"[a-z0-9#+.]+", kw)
    if len(parts) > 1:
        return all(p in text for p in parts)
    return False


def _collect_keywords(jd_analysis: dict) -> list[str]:
    seen: set[str] = set()
    keywords: list[str] = []
    for key in ("keywords", "required_skills"):
        for item in jd_analysis.get(key) or []:
            if not isinstance(item, str):
                continue
            norm = _normalize_keyword(item)
            if norm and norm not in seen:
                seen.add(norm)
                keywords.append(item.strip())
    return keywords


def _score_keywords(keywords: list[str], resume_lower: str) -> tuple[int, list[str], list[str]]:
    if not keywords:
        return 70, [], []
    matched = [k for k in keywords if _keyword_in_text(k, resume_lower)]
    missing = [k for k in keywords if k not in matched]
    pct = int(len(matched) / len(keywords) * 100)
    return pct, matched, missing


def _score_skills(required_skills: list[str], resume_lower: str) -> tuple[int, list[str], list[str]]:
    if not required_skills:
        return 70, [], []
    matched = [s for s in required_skills if _keyword_in_text(s, resume_lower)]
    missing = [s for s in required_skills if s not in matched]
    pct = int(len(matched) / len(required_skills) * 100)
    return pct, matched, missing


def _score_sections(content: ResumeContent) -> int:
    checks = [
        bool(content.summary.strip()),
        len(content.experience) > 0,
        len(content.education) > 0,
        any(cat.skills for cat in content.skills),
        bool(content.contact.full_name.strip()),
        bool(content.contact.email.strip()),
    ]
    return int(sum(checks) / len(checks) * 100)


def _score_formatting(content: ResumeContent) -> int:
    score = 100
    if not content.contact.full_name.strip():
        score -= 25
    if not content.contact.email.strip():
        score -= 15
    if not content.experience:
        score -= 30
    else:
        has_bullets = any(exp.bullets for exp in content.experience)
        if not has_bullets:
            score -= 20
        dated = sum(1 for exp in content.experience if exp.start_date)
        if dated < len(content.experience):
            score -= 10
    if not content.summary.strip():
        score -= 10
    return max(0, min(100, score))


def _build_suggestions(
    missing_keywords: list[str],
    missing_skills: list[str],
    content: ResumeContent,
    section_score: int,
) -> list[str]:
    suggestions: list[str] = []
    if missing_keywords:
        suggestions.append(f"Add missing keywords: {', '.join(missing_keywords[:8])}")
    if missing_skills:
        extra = [s for s in missing_skills if s not in missing_keywords]
        if extra:
            suggestions.append(f"Highlight required skills: {', '.join(extra[:6])}")
    if not content.summary.strip():
        suggestions.append("Add a tailored professional summary aligned with the job description")
    if section_score < 80:
        suggestions.append("Complete all resume sections (summary, experience, education, skills, contact)")
    exp = content.experience
    if exp and not any(e.bullets for e in exp):
        suggestions.append("Add bullet points under experience with metrics and action verbs")
    return suggestions


def score_resume(content: dict, job_description: str, jd_analysis: dict | None = None) -> ATSResult:
    """Score resume content against JD analysis and raw job description."""
    jd_analysis = jd_analysis or {}
    resume = ResumeContent.model_validate(content or {})
    resume_text = resume_to_text(resume)
    resume_lower = resume_text.lower()

    keywords = _collect_keywords(jd_analysis)
    keyword_match, matched_kw, missing_kw = _score_keywords(keywords, resume_lower)

    semantic_raw = tfidf_score(resume_text, job_description)
    semantic_score = int(min(100, semantic_raw.get("score", 0)))

    required_skills = [s for s in (jd_analysis.get("required_skills") or []) if isinstance(s, str)]
    skills_coverage, _, missing_skills = _score_skills(required_skills, resume_lower)

    section_score = _score_sections(resume)
    formatting_score = _score_formatting(resume)

    overall = int(
        keyword_match * WEIGHTS["keyword"]
        + semantic_score * WEIGHTS["semantic"]
        + skills_coverage * WEIGHTS["skills"]
        + section_score * WEIGHTS["section"]
        + formatting_score * WEIGHTS["formatting"]
    )

    suggestions = _build_suggestions(missing_kw, missing_skills, resume, section_score)

    breakdown = {
        "weights": WEIGHTS,
        "keyword": {"score": keyword_match, "matched": len(matched_kw), "total": len(keywords)},
        "semantic": {"score": semantic_score, "matched_tokens": semantic_raw.get("matched_keywords", [])[:15]},
        "skills": {"score": skills_coverage, "required": len(required_skills)},
        "section": {"score": section_score},
        "formatting": {"score": formatting_score},
    }

    return ATSResult(
        overall_score=overall,
        keyword_match=keyword_match,
        formatting_score=formatting_score,
        semantic_score=semantic_score,
        skills_coverage=skills_coverage,
        section_score=section_score,
        matched_keywords=matched_kw,
        missing_keywords=missing_kw,
        suggestions=suggestions,
        breakdown=breakdown,
    )
