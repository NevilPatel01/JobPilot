"""Robust JSON extraction from LLM responses.

Models frequently wrap JSON in ```json code fences or add a sentence of prose.
Naive json.loads on that raises "Expecting value: line 1 column 1 (char 0)".
"""

import json
import re


def extract_json_object(raw: str) -> dict:
    """Best-effort parse of a JSON object out of an LLM response.

    Strips code fences and falls back to the first balanced {...} block.
    Raises ValueError with a user-friendly message when nothing parses.
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
