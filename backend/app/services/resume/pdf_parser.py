from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.llm.client import LLMConfig

logger = logging.getLogger(__name__)


@dataclass
class PdfParseResult:
    content: dict
    warnings: list[str]
    confidence: float
    section_counts: dict[str, int]


def compute_section_counts(content: dict) -> dict[str, int]:
    contact = content.get("contact") or {}
    return {
        "experience": len(content.get("experience") or []),
        "education": len(content.get("education") or []),
        "projects": len(content.get("projects") or []),
        "skill_categories": len(content.get("skills") or []),
        "links": len(content.get("links") or []),
        "has_summary": 1 if (content.get("summary") or "").strip() else 0,
        "has_contact_name": 1 if (contact.get("full_name") or "").strip() else 0,
    }


def _parse_pdf_stub(raw: str) -> PdfParseResult:
    from app.schemas.resume_content import ResumeContent

    content = ResumeContent()
    warnings: list[str] = []
    if raw.strip():
        content.summary = raw[:2000]
        warnings.append("No API key — only summary text was extracted. Review all sections in your profile.")
        confidence = 0.25
    else:
        warnings.append("Could not extract text from PDF.")
        confidence = 0.0
    dumped = content.model_dump()
    return PdfParseResult(
        content=dumped,
        warnings=warnings,
        confidence=confidence,
        section_counts=compute_section_counts(dumped),
    )


def _extract_json_from_llm(raw: str) -> str:
    text = raw.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    return match.group(1).strip() if match else text


_PARSE_PROMPT = """\
Extract every piece of resume data from the text below and return a single JSON object.

REQUIRED JSON STRUCTURE (use exact field names):
{{
  "content": {{
    "contact": {{
      "full_name": "First Last",
      "email": "user@example.com",
      "phone": "+1 555-000-0000",
      "location": "City, Province/State"
    }},
    "links": [
      {{"label": "LinkedIn", "url": "https://linkedin.com/in/..."}},
      {{"label": "GitHub",   "url": "https://github.com/..."}},
      {{"label": "Portfolio","url": "https://..."}}
    ],
    "summary": "Full professional summary paragraph from the resume.",
    "experience": [
      {{
        "title": "Job Title",
        "company": "Employer Name",
        "location": "City, Province",
        "start_date": "Mon YYYY",
        "end_date": "Mon YYYY or Present",
        "bullets": [
          "Exact bullet point from the resume",
          "Another bullet point — keep metrics and wording intact"
        ]
      }}
    ],
    "education": [
      {{
        "institution": "University or College Name",
        "degree": "Degree and Field of Study",
        "location": "City, Province",
        "start_date": "Mon YYYY",
        "end_date": "Mon YYYY",
        "gpa": "3.9 or empty string if not listed"
      }}
    ],
    "projects": [
      {{
        "name": "Project Name",
        "url": "https://github.com/... or empty string",
        "bullets": ["What the project does or what you built"]
      }}
    ],
    "skills": [
      {{"name": "Languages",   "skills": ["Python", "TypeScript"]}},
      {{"name": "Frameworks",  "skills": ["React", "FastAPI"]}},
      {{"name": "Tools",       "skills": ["Docker", "PostgreSQL"]}}
    ]
  }},
  "warnings": ["list any ambiguous or missing sections here"],
  "confidence": 0.85
}}

EXTRACTION RULES:
- Include ALL jobs, ALL education entries, ALL projects, ALL skill groups found
- Preserve bullet wording exactly — do not paraphrase or shorten
- Extract LinkedIn / GitHub / portfolio URLs from the header or contact section into links[]
- Keep every numeric metric (%, $, x) exactly as written
- Use empty string "" for any field not found — never omit a field
- confidence: 0.9+ if all main sections present, 0.6-0.9 if some missing, below 0.6 if very sparse
- Return raw JSON only — no markdown, no explanation

RESUME TEXT:
{raw}"""


async def parse_pdf_text(raw: str, llm_config: LLMConfig | None = None) -> PdfParseResult:
    if not raw.strip():
        return _parse_pdf_stub(raw)

    if not llm_config:
        return _parse_pdf_stub(raw)

    from langchain_core.messages import HumanMessage, SystemMessage

    from app.agents.retry import invoke_llm
    from app.schemas.resume_content import ResumeContent
    from app.services.llm.client import create_chat_model

    prompt = _PARSE_PROMPT.format(raw=raw[:15000])
    raw_response = ""

    try:
        llm = create_chat_model(llm_config, temperature=0.0)
        res = await invoke_llm(
            llm,
            [
                SystemMessage(content="You are a precise resume parser. Return raw JSON only — no markdown, no explanation."),
                HumanMessage(content=prompt),
            ],
        )
        raw_response = res.content if isinstance(res.content, str) else str(res.content)
        json_text = _extract_json_from_llm(raw_response)
        parsed = json.loads(json_text)
        content = ResumeContent.model_validate(parsed.get("content") or {})
        warnings = [str(w) for w in (parsed.get("warnings") or []) if w]
        confidence = float(parsed.get("confidence", 0.7))
        confidence = max(0.0, min(1.0, confidence))

        counts = compute_section_counts(content.model_dump())
        if not counts["has_contact_name"]:
            warnings.append("Contact name was not detected — verify the header in your profile.")
        if counts["experience"] == 0:
            warnings.append("No experience entries found — add roles manually if missing.")
        if counts["education"] == 0:
            warnings.append("No education entries found — add degrees manually if missing.")

        return PdfParseResult(
            content=content.model_dump(),
            warnings=warnings or ["Review parsed sections for accuracy."],
            confidence=confidence,
            section_counts=counts,
        )
    except Exception as e:
        logger.warning("LLM PDF parse failed (response: %.200s): %s", raw_response, e)
        stub = _parse_pdf_stub(raw)
        stub.warnings.insert(0, f"Structured parse failed ({e}); using summary-only fallback.")
        stub.confidence = min(stub.confidence, 0.3)
        return stub
