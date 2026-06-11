import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.retry import invoke_llm
from app.services.llm.client import LLMConfig, create_chat_model

logger = logging.getLogger(__name__)


async def enrich_company_research(research: dict, llm_config: LLMConfig | None) -> dict:
    """Add structured LLM summary to company research payload."""
    if not llm_config or not research.get("raw_text"):
        return research

    llm = create_chat_model(llm_config, temperature=0.2)
    prompt = f"""Summarize this company research text as JSON with keys:
- mission: string
- products: list of strings
- values: list of strings
- tech_stack: list of strings (infer if mentioned)

Text:
{research['raw_text'][:8000]}"""

    try:
        res = await invoke_llm(
            llm,
            [SystemMessage(content="Return valid JSON only."), HumanMessage(content=prompt)],
        )
        parsed = json.loads(res.content if isinstance(res.content, str) else str(res.content))
        research = {**research, **parsed}
        parts = [parsed.get("mission", "")]
        if parsed.get("products"):
            parts.append("Products: " + ", ".join(parsed["products"][:5]))
        if parsed.get("tech_stack"):
            parts.append("Tech: " + ", ".join(parsed["tech_stack"][:8]))
        research["summary"] = "\n".join(p for p in parts if p)[:2000]
    except Exception as e:
        logger.warning("Company LLM summary failed: %s", e)

    return research
