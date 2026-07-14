"""LLM extraction: raw resume text → draft candidate facts.

Anti-hallucination gate: every draft must carry a verbatim source_excerpt found
in the input text; drafts whose excerpt is absent are rejected deterministically
(no second LLM call). One schema-retry with the validation error appended, then
give up with a warning. Nothing here persists facts — drafts go back to the UI
for user review (POST /candidate/import/confirm persists the accepted ones)."""

import json
import logging
import re
from dataclasses import dataclass, field
from uuid import UUID

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field, ValidationError

from app.agents.json_utils import extract_json_object
from app.agents.retry import invoke_llm
from app.schemas.candidate import CandidateFactCreate, FactType
from app.services.audit import record_audit_event
from app.services.llm.client import create_chat_model, get_user_llm_config

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT_VERSION = "fx-v1"
MAX_INPUT_CHARS = 6000

_SYSTEM_PROMPT = (
    "Extract candidate facts from the resume text. Return JSON: "
    '{"facts": [{"fact_type": "...", "payload": {...}, "source_excerpt": "..."}]}. '
    "fact_type is one of employment, education, certification, skill, project. "
    "Payload keys — employment: employer, title, start_date, end_date, location, summary; "
    "education: institution, credential, field_of_study; certification: name, issuer; "
    "skill: name; project: name, url, one_liner, highlights. "
    "source_excerpt must be a short verbatim substring of the input that evidences the fact. "
    "Only extract information explicitly present. Do not infer skills from job titles. "
    "Dates must be ISO (YYYY-MM-DD) or omitted."
)


class DraftFactItem(BaseModel):
    fact_type: FactType
    payload: dict = Field(..., max_length=50)
    source_excerpt: str = Field(..., min_length=3, max_length=500)


@dataclass
class ExtractionResult:
    draft_facts: list[CandidateFactCreate] = field(default_factory=list)
    rejected: int = 0
    warning: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).casefold().strip()


def _usage(message) -> tuple[int, int]:
    usage = getattr(message, "usage_metadata", None) or {}
    return int(usage.get("input_tokens") or 0), int(usage.get("output_tokens") or 0)


def _parse_drafts(raw_content: str, source_text: str) -> tuple[list[CandidateFactCreate], int]:
    data = extract_json_object(raw_content)
    items = data.get("facts")
    if not isinstance(items, list):
        raise ValueError('response is missing a "facts" list')
    haystack = _normalize(source_text)
    drafts: list[CandidateFactCreate] = []
    rejected = 0
    for item in items:
        parsed = DraftFactItem.model_validate(item)  # raises ValidationError → retry path
        if _normalize(parsed.source_excerpt) not in haystack:
            rejected += 1
            continue
        drafts.append(
            CandidateFactCreate(fact_type=parsed.fact_type, payload=parsed.payload, source="resume_upload")
        )
    return drafts, rejected


async def extract_facts_from_resume_text(
    db,
    user_id: UUID,
    text: str,
    *,
    chat_model=None,
    model_name: str | None = None,
) -> ExtractionResult:
    trimmed = (text or "").strip()[:MAX_INPUT_CHARS]
    if not trimmed:
        return ExtractionResult(warning="No resume text provided.")

    if chat_model is None:
        llm_config = await get_user_llm_config(db, user_id)
        if not llm_config:
            return ExtractionResult(warning="No LLM API key configured — add one in Settings.")
        chat_model = create_chat_model(llm_config, temperature=0.0)
        model_name = model_name or llm_config.model_name

    result = ExtractionResult()
    messages = [SystemMessage(content=_SYSTEM_PROMPT), HumanMessage(content=trimmed)]
    for attempt in (1, 2):
        response = await invoke_llm(chat_model, messages)
        input_tokens, output_tokens = _usage(response)
        result.input_tokens += input_tokens
        result.output_tokens += output_tokens
        try:
            result.draft_facts, result.rejected = _parse_drafts(response.content, trimmed)
            result.warning = None
            break
        except (ValueError, ValidationError, json.JSONDecodeError) as exc:
            logger.warning("fact extraction parse failed (attempt %s): %s", attempt, exc)
            result.warning = f"Extraction failed: {exc}"
            if attempt == 1:
                messages = messages + [
                    HumanMessage(content=f"Your previous response failed validation: {exc}. "
                                         "Return only the corrected JSON object.")
                ]

    await record_audit_event(
        db,
        user_id=user_id,
        action="candidate_fact.extraction",
        entity_type="users",
        entity_id=str(user_id),
        model_name=model_name,
        prompt_version=EXTRACTION_PROMPT_VERSION,
        after={
            "drafts": len(result.draft_facts),
            "rejected": result.rejected,
            "input_tokens": result.input_tokens,
            "output_tokens": result.output_tokens,
            "warning": result.warning,
        },
    )
    return result
