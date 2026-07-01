import json

from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.editor_agent import _get_by_path, apply_change, extract_json_object
from app.agents.retry import invoke_llm
from app.services.llm.client import create_chat_model, get_user_llm_config

__all__ = ["run_cover_letter_agent", "apply_change"]


async def run_cover_letter_agent(
    db: AsyncSession,
    user_id,
    content: dict,
    message: str,
    job_description: str = "",
    company_summary: str = "",
) -> tuple[str, list[dict]]:
    llm_config = await get_user_llm_config(db, user_id)
    if not llm_config:
        return "Please configure an API key in Settings to use AI editing.", []

    llm = create_chat_model(llm_config)

    prompt = f"""User wants to edit their cover letter. Current content JSON:
{json.dumps(content)[:6000]}

Job description: {job_description[:2000]}
Company context: {company_summary[:1500]}
User request: {message}

Return JSON with:
- reply: string (brief explanation)
- changes: list of {{path, old_value, new_value}} using paths like paragraphs[0], salutation, closing, recipient_name
Only suggest changes needed. Max 3 changes. Keep total letter length between 250-400 words when editing paragraphs."""

    try:
        res = await invoke_llm(
            llm,
            [
                SystemMessage(content="You are a cover letter editor. Return ONLY a raw JSON object — no markdown, no code fences, no prose."),
                HumanMessage(content=prompt),
            ],
        )
        parsed = extract_json_object(res.content if isinstance(res.content, str) else str(res.content))
        changes = []
        for ch in parsed.get("changes", []):
            path = ch.get("path", "")
            old = ch.get("old_value") or str(_get_by_path(content, path))
            new = ch.get("new_value", "")
            changes.append({"path": path, "old_value": old, "new_value": new, "status": "pending"})
        return parsed.get("reply", "Here are my suggested changes."), changes
    except Exception as e:
        return f"I couldn't process that request: {e}", []
