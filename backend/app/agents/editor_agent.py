import json
from copy import deepcopy
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.resume_content import ResumeContent
from app.services.llm.client import create_chat_model, get_user_llm_config
from app.services.rag.ingest import search_chunks


def _get_by_path(obj: dict, path: str) -> Any:
    parts = path.replace("]", "").split("[")
    current: Any = obj
    for part in parts:
        if not part:
            continue
        if "." in part:
            for key in part.split("."):
                if key:
                    current = current[int(key)] if key.isdigit() else current.get(key, "")
        elif part.isdigit():
            current = current[int(part)]
        else:
            current = current.get(part, "")
    return current


def _set_by_path(obj: dict, path: str, value: Any) -> None:
    parts = path.replace("]", "").split("[")
    current = obj
    keys: list = []
    for part in parts:
        if not part:
            continue
        for key in part.split("."):
            if key:
                keys.append(int(key) if key.isdigit() else key)

    for key in keys[:-1]:
        if isinstance(key, int):
            current = current[key]
        else:
            if key not in current:
                current[key] = {}
            current = current[key]

    last = keys[-1]
    if isinstance(last, int):
        current[last] = value
    else:
        current[last] = value


async def run_editor_agent(
    db: AsyncSession,
    user_id,
    content: dict,
    message: str,
    job_description: str = "",
) -> tuple[str, list[dict]]:
    llm_config = await get_user_llm_config(db, user_id)
    if not llm_config:
        return "Please configure an API key in Settings to use AI editing.", []

    chunks = await search_chunks(db, user_id, message + " " + job_description, llm_config)
    rag = "\n".join(c.chunk_text for c in chunks[:4])
    llm = create_chat_model(llm_config)

    prompt = f"""User wants to edit their resume. Current content JSON:
{json.dumps(content)[:8000]}

Job context: {job_description[:2000]}
RAG: {rag[:2000]}
User request: {message}

Return JSON with:
- reply: string (brief explanation)
- changes: list of {{path, old_value, new_value}} using dot/bracket paths like experience[0].bullets[1]
Only suggest changes needed. Max 3 changes."""

    try:
        res = await llm.ainvoke([SystemMessage(content="Return valid JSON only."), HumanMessage(content=prompt)])
        parsed = json.loads(res.content if isinstance(res.content, str) else str(res.content))
        changes = []
        for ch in parsed.get("changes", []):
            path = ch.get("path", "")
            old = ch.get("old_value") or str(_get_by_path(content, path))
            new = ch.get("new_value", "")
            changes.append({"path": path, "old_value": old, "new_value": new, "status": "pending"})
        return parsed.get("reply", "Here are my suggested changes."), changes
    except Exception as e:
        return f"I couldn't process that request: {e}", []


def apply_change(content: dict, path: str, new_value: str) -> dict:
    updated = deepcopy(content)
    _set_by_path(updated, path, new_value)
    return updated
