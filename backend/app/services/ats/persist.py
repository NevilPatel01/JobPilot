"""Persist ATS scores with optional LLM-enriched suggestions."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resume import ATSScore, ResumeDocument
from app.services.ats.llm_suggestions import enrich_suggestions_with_llm
from app.services.ats.scorer import ATSResult, score_resume
from app.services.ats.suggestions import build_rule_based_items
from app.services.llm.client import get_user_llm_config


def suggestions_json_from_result(result: ATSResult, items: list[dict]) -> dict:
    texts = [item["text"] for item in items] if items else result.suggestions
    return {"suggestions": texts, "items": items}


async def build_ats_result_with_suggestions(
    db: AsyncSession,
    user_id: UUID,
    content: dict,
    job_description: str,
    jd_analysis: dict | None,
    *,
    enrich_llm: bool = True,
) -> tuple[ATSResult, list[dict]]:
    result = score_resume(content, job_description, jd_analysis or {})
    items = build_rule_based_items(result)

    if enrich_llm:
        llm_config = await get_user_llm_config(db, user_id)
        if llm_config:
            items = await enrich_suggestions_with_llm(result, job_description, jd_analysis or {}, llm_config)

    return result, items


async def save_ats_score(
    db: AsyncSession,
    resume: ResumeDocument,
    user_id: UUID,
    *,
    enrich_llm: bool = True,
) -> ATSScore:
    jd_analysis = (resume.insights_json or {}).get("jd_analysis", {})
    result, items = await build_ats_result_with_suggestions(
        db,
        user_id,
        resume.content_json or {},
        resume.job_description or "",
        jd_analysis,
        enrich_llm=enrich_llm,
    )
    payload = suggestions_json_from_result(result, items)
    row = ATSScore(
        resume_id=resume.id,
        job_description=resume.job_description,
        overall_score=result.overall_score,
        keyword_match=result.keyword_match,
        formatting_score=result.formatting_score,
        semantic_score=result.semantic_score,
        skills_coverage=result.skills_coverage,
        section_score=result.section_score,
        matched_keywords=result.matched_keywords,
        suggestions_json=payload,
        breakdown_json=result.breakdown,
        missing_keywords=result.missing_keywords,
    )
    db.add(row)
    await db.flush()
    await db.refresh(row)
    return row
