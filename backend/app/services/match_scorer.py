import re
from collections import Counter


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9#+.]+", text.lower())


def extract_skills(resume_text: str) -> list[str]:
    tokens = tokenize(resume_text)
    stop = {"the", "and", "for", "with", "from", "this", "that", "have", "been", "will", "your"}
    return list(dict.fromkeys(t for t in tokens if len(t) > 2 and t not in stop))[:50]


def tfidf_score(resume_text: str, job_description: str) -> dict:
    try:
        resume_tokens = set(tokenize(resume_text))
        job_tokens = tokenize(job_description or "")
        job_freq = Counter(job_tokens)
        matched = [t for t in job_freq if t in resume_tokens]
        score = min(100, round(len(matched) / max(len(set(job_tokens)), 1) * 100, 1))
        return {"score": score, "matched_keywords": matched[:20]}
    except Exception:
        return {"score": 0, "matched_keywords": []}
