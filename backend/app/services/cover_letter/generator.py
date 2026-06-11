"""Cover letter generation helpers — prompts and length enforcement."""

from __future__ import annotations

import json
from typing import Any

MIN_WORDS = 250
MAX_WORDS = 400
TARGET_PARAGRAPHS = (3, 4)


def word_count(paragraphs: list[str]) -> int:
    return sum(len(p.split()) for p in paragraphs if p)


def enforce_word_limits(paragraphs: list[str], *, min_words: int = MIN_WORDS, max_words: int = MAX_WORDS) -> list[str]:
    """Trim or pad lightly so generated letters stay within ATS-friendly length."""
    if not paragraphs:
        return paragraphs

    cleaned = [p.strip() for p in paragraphs if p and p.strip()]
    if not cleaned:
        return paragraphs

    total = word_count(cleaned)
    if total <= max_words:
        return cleaned

    trimmed: list[str] = []
    running = 0
    for para in cleaned:
        words = para.split()
        if running + len(words) <= max_words:
            trimmed.append(para)
            running += len(words)
        else:
            remaining = max_words - running
            if remaining > 40:
                trimmed.append(" ".join(words[:remaining]))
            break

    return trimmed or cleaned[:1]


def _company_context(company: dict[str, Any]) -> str:
    bits = {k: company.get(k) for k in ("company_name", "mission", "products", "values", "tech_stack", "summary") if company.get(k)}
    return json.dumps(bits)[:2500]


def _jd_context(jd_analysis: dict[str, Any]) -> str:
    if not jd_analysis:
        return ""
    keys = ("role_title", "keywords", "required_skills", "responsibilities", "qualifications", "sections")
    bits = {k: jd_analysis.get(k) for k in keys if jd_analysis.get(k)}
    return json.dumps(bits)[:2000]


def build_cover_letter_prompt(
    *,
    meta: dict[str, Any],
    company: dict[str, Any],
    jd_analysis: dict[str, Any],
    job_description: str,
    resume_text: str,
) -> str:
    hiring_manager = meta.get("hiring_manager_name") or "Hiring Manager"
    role_title = jd_analysis.get("role_title") or company.get("role_title") or "the role"
    company_name = company.get("company_name") or meta.get("company_name") or "the company"
    additional = meta.get("additional_context") or ""

    return f"""Write a tailored cover letter as JSON with keys:
- paragraphs: list of {TARGET_PARAGRAPHS[0]}-{TARGET_PARAGRAPHS[1]} strings (each a full paragraph)
- closing: string (e.g. "Sincerely,")

Requirements:
- Total length: {MIN_WORDS}-{MAX_WORDS} words across all paragraphs
- Tone: professional, confident, specific — avoid clichés and filler
- Paragraph 1: hook — role + company fit in 2-3 sentences
- Middle paragraph(s): map 2-3 resume achievements to JD requirements with metrics where possible
- Final paragraph: clear interest + call to action (interview / conversation)
- Reference the company naturally using research below; do not invent facts not supported by context
- Do not repeat the resume verbatim; complement it

Recipient: {hiring_manager}
Target role: {role_title}
Company: {company_name}
User notes: {additional[:800]}

Job description excerpt:
{job_description[:2500]}

JD analysis:
{_jd_context(jd_analysis)}

Company research:
{_company_context(company)}

Candidate resume (for achievement mapping only):
{resume_text[:3500]}"""


def parse_cover_letter_response(raw: dict[str, Any]) -> tuple[list[str], str]:
    paragraphs = raw.get("paragraphs") or []
    if isinstance(paragraphs, str):
        paragraphs = [paragraphs]
    paragraphs = [str(p).strip() for p in paragraphs if str(p).strip()]
    paragraphs = enforce_word_limits(paragraphs)
    closing = str(raw.get("closing") or "Sincerely,").strip() or "Sincerely,"
    return paragraphs, closing
