import re

CHUNK_SIZE = 800
CHUNK_OVERLAP = 100


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    text = re.sub(r"\s+", " ", text.strip())
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end - overlap
        if start >= len(text):
            break
    return chunks


def chunk_resume_content(content: dict) -> list[tuple[str, str]]:
    """Return list of (source_label, chunk_text) from structured resume."""
    parts: list[tuple[str, str]] = []

    contact = content.get("contact", {})
    if contact:
        contact_text = " ".join(str(v) for v in contact.values() if v)
        if contact_text:
            parts.append(("contact", contact_text))

    if content.get("summary"):
        parts.append(("summary", content["summary"]))

    for i, exp in enumerate(content.get("experience", [])):
        bullets = "\n".join(exp.get("bullets", []))
        text = f"{exp.get('title', '')} at {exp.get('company', '')}\n{bullets}"
        parts.append((f"experience_{i}", text))

    for i, edu in enumerate(content.get("education", [])):
        text = f"{edu.get('degree', '')} {edu.get('institution', '')}"
        parts.append((f"education_{i}", text))

    for i, proj in enumerate(content.get("projects", [])):
        bullets = "\n".join(proj.get("bullets", []))
        text = f"{proj.get('name', '')}\n{bullets}"
        parts.append((f"project_{i}", text))

    for i, cat in enumerate(content.get("skills", [])):
        text = f"{cat.get('name', '')}: {', '.join(cat.get('skills', []))}"
        parts.append((f"skills_{i}", text))

    return parts
