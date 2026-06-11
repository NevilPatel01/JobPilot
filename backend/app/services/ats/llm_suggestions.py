"""LLM-enhanced ATS improvement suggestions."""

from __future__ import annotations

import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.retry import invoke_llm
from app.services.ats.scorer import ATSResult
from app.services.ats.suggestions import build_rule_based_items
from app.services.llm.client import LLMConfig, create_chat_model

logger = logging.getLogger(__name__)


async def enrich_suggestions_with_llm(
    result: ATSResult,
    job_description: str,
    jd_analysis: dict,
    llm_config: LLMConfig,
) -> list[dict]:
    fallback = build_rule_based_items(result)
    if result.overall_score >= 85 and not result.missing_keywords:
        return fallback[:5]

    llm = create_chat_model(llm_config, temperature=0.3)
    prompt = f"""Given this ATS analysis, return JSON with key "items": a list of up to 5 objects.
Each object must have: text (string), prompt (string, actionable chat instruction for a resume editor), priority (high|medium|low), category (keyword|skills|section|semantic|formatting|general).

Job description excerpt:
{job_description[:2500]}

JD analysis: {json.dumps(jd_analysis)[:1500]}
Overall score: {result.overall_score}
Missing keywords: {result.missing_keywords[:12]}
Matched keywords: {result.matched_keywords[:12]}
Dimension scores: keyword={result.keyword_match}, semantic={result.semantic_score}, skills={result.skills_coverage}, sections={result.section_score}, formatting={result.formatting_score}

Focus on the highest-impact fixes first."""

    try:
        res = await invoke_llm(
            llm,
            [SystemMessage(content="Return valid JSON only."), HumanMessage(content=prompt)],
        )
        parsed = json.loads(res.content if isinstance(res.content, str) else str(res.content))
        items = parsed.get("items", [])
        cleaned: list[dict] = []
        for item in items:
            if not isinstance(item, dict) or not item.get("text"):
                continue
            cleaned.append(
                {
                    "text": str(item["text"]),
                    "prompt": str(item.get("prompt") or item["text"]),
                    "priority": str(item.get("priority") or "medium"),
                    "category": str(item.get("category") or "general"),
                }
            )
        return cleaned[:5] if cleaned else fallback[:5]
    except Exception as e:
        logger.warning("LLM ATS suggestions failed: %s", e)
        return fallback[:5]
