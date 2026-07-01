import json
import re
from copy import deepcopy
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.retry import invoke_llm
from app.services.llm.client import create_chat_model, get_user_llm_config
from app.services.rag.ingest import search_chunks


def extract_json_object(raw: str) -> dict:
    """Best-effort parse of a JSON object out of an LLM response.

    Models frequently wrap JSON in ```json code fences or add a sentence of
    prose. Naive json.loads on that raises "Expecting value: line 1 column 1".
    This strips fences and falls back to the first balanced {...} block.
    """
    text = (raw or "").strip()
    if not text:
        raise ValueError("The AI returned an empty response. Please try again.")

    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if fenced:
        text = fenced.group(1).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Fall back to the first balanced top-level object.
    start = text.find("{")
    if start != -1:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    return json.loads(text[start : i + 1])
    raise ValueError("The AI response was not valid JSON. Please rephrase your request.")


_SECTION_LABELS = {
    "contact": "Contact",
    "links": "Links",
    "summary": "Summary",
    "experience": "Experience",
    "education": "Education",
    "projects": "Projects",
    "skills": "Skills",
}

_FIELD_LABELS = {
    "full_name": "Name",
    "email": "Email",
    "phone": "Phone",
    "location": "Location",
    "label": "Label",
    "url": "URL",
    "company": "Company",
    "title": "Title",
    "start_date": "Start date",
    "end_date": "End date",
    "bullets": "Bullets",
    "institution": "Institution",
    "degree": "Degree",
    "gpa": "GPA",
    "name": "Name",
    "skills": "Skills list",
}


def coerce_change_value(value: Any) -> Any:
    """Normalize a diff value for apply_change (supports JSON strings and collections)."""
    if isinstance(value, (list, dict, bool, int, float)) or value is None:
        return value
    if not isinstance(value, str):
        return value
    stripped = value.strip()
    if not stripped:
        return ""
    if stripped[0] in "[{" or stripped in ("true", "false", "null"):
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            pass
    return value


def serialize_diff_value(value: Any) -> str | None:
    """Store diff values as text while preserving list/dict structure."""
    if value is None:
        return None
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def format_path_label(content: dict, path: str) -> str:
    """Turn a JSON path into a human-readable label for the editor UI."""
    parts = path.replace("]", "").split("[")
    tokens: list[str | int] = []
    for part in parts:
        if not part:
            continue
        for key in part.split("."):
            if key:
                tokens.append(int(key) if key.isdigit() else key)

    if not tokens:
        return path

    labels: list[str] = []
    cursor: Any = content

    for idx, token in enumerate(tokens):
        if isinstance(token, str):
            label = _SECTION_LABELS.get(token) or _FIELD_LABELS.get(token) or token.replace("_", " ").title()
            labels.append(label)
            if isinstance(cursor, dict):
                cursor = cursor.get(token, [])
            continue

        prev = tokens[idx - 1] if idx > 0 else None
        if prev == "experience" and isinstance(cursor, list) and token < len(cursor):
            entry = cursor[token]
            detail = entry.get("company") or entry.get("title") or f"Entry {token + 1}"
            labels[-1] = f"Experience · {detail}"
            cursor = entry
        elif prev == "education" and isinstance(cursor, list) and token < len(cursor):
            entry = cursor[token]
            detail = entry.get("institution") or entry.get("degree") or f"Entry {token + 1}"
            labels[-1] = f"Education · {detail}"
            cursor = entry
        elif prev == "projects" and isinstance(cursor, list) and token < len(cursor):
            entry = cursor[token]
            detail = entry.get("name") or f"Project {token + 1}"
            labels[-1] = f"Projects · {detail}"
            cursor = entry
        elif prev == "skills" and isinstance(cursor, list) and token < len(cursor):
            entry = cursor[token]
            detail = entry.get("name") or f"Category {token + 1}"
            labels[-1] = f"Skills · {detail}"
            cursor = entry
        elif prev == "links" and isinstance(cursor, list) and token < len(cursor):
            entry = cursor[token]
            detail = entry.get("label") or f"Link {token + 1}"
            labels[-1] = f"Links · {detail}"
            cursor = entry
        elif prev == "bullets":
            if labels and labels[-1] == "Bullets":
                labels.pop()
            labels.append(f"Bullet {token + 1}")
            if isinstance(cursor, list) and token < len(cursor):
                cursor = cursor[token]
        else:
            labels.append(f"Item {token + 1}")
            if isinstance(cursor, list) and token < len(cursor):
                cursor = cursor[token]

    deduped: list[str] = []
    for label in labels:
        if not deduped or deduped[-1] != label:
            deduped.append(label)
    return " · ".join(deduped)


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
        res = await invoke_llm(
            llm,
            [
                SystemMessage(content="You are a resume editor. Return ONLY a raw JSON object — no markdown, no code fences, no prose."),
                HumanMessage(content=prompt),
            ],
        )
        parsed = extract_json_object(res.content if isinstance(res.content, str) else str(res.content))
        changes = []
        for ch in parsed.get("changes", []):
            path = ch.get("path", "")
            raw_old = ch.get("old_value")
            raw_new = ch.get("new_value", "")
            if raw_old is None:
                raw_old = _get_by_path(content, path)
            old = serialize_diff_value(raw_old)
            new = serialize_diff_value(coerce_change_value(raw_new))
            changes.append({"path": path, "old_value": old, "new_value": new, "status": "pending"})
        return parsed.get("reply", "Here are my suggested changes."), changes
    except Exception as e:
        return f"I couldn't process that request: {e}", []


def apply_change(content: dict, path: str, new_value: Any) -> dict:
    updated = deepcopy(content)
    _set_by_path(updated, path, coerce_change_value(new_value))
    return updated
