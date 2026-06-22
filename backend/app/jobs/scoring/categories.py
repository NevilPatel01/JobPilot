from dataclasses import dataclass


CATEGORY_LABELS = {
    "it_support": "IT Support / End User Support",
    "cloud_junior_devops": "Cloud Support / Junior DevOps",
    "fullstack_web": "Full-stack / Web Developer",
    "app_support_analyst": "Application Support / Technical Analyst",
    "automation_scada": "Automation / SCADA-adjacent",
}

CATEGORY_KEYWORDS = {
    "it_support": {
        "help desk", "helpdesk", "desktop support", "it support", "end user", "active directory",
        "microsoft 365", "windows", "ticketing", "hardware", "technical support",
    },
    "cloud_junior_devops": {
        "aws", "azure", "gcp", "cloud", "devops", "docker", "kubernetes", "terraform", "linux",
        "ci/cd", "infrastructure", "site reliability", "noc",
    },
    "fullstack_web": {
        "full stack", "fullstack", "frontend", "backend", "react", "next.js", "typescript", "javascript",
        "python", "fastapi", "django", "node.js", "api", "web developer",
    },
    "app_support_analyst": {
        "application support", "support analyst", "technical analyst", "business systems", "sql",
        "incident", "problem management", "servicenow", "troubleshooting", "production support",
    },
    "automation_scada": {
        "scada", "plc", "automation", "control systems", "industrial", "hmi", "ignition", "modbus",
        "rockwell", "siemens",
    },
}


@dataclass(frozen=True)
class CategoryRecommendation:
    category: str
    confidence: int
    matched_terms: tuple[str, ...]


def recommend_category(title: str, description: str, skills: list[str]) -> CategoryRecommendation:
    title_text = title.casefold()
    description_text = description.casefold()
    skill_text = " ".join(skills).casefold()
    scores: dict[str, int] = {}
    matches: dict[str, list[str]] = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        points = 0
        found: list[str] = []
        for keyword in keywords:
            if keyword in title_text:
                points += 4
                found.append(keyword)
            elif keyword in skill_text:
                points += 2
                found.append(keyword)
            elif keyword in description_text:
                points += 1
                found.append(keyword)
        scores[category] = points
        matches[category] = found

    category = max(scores, key=scores.get)
    best = scores[category]
    ordered = sorted(scores.values(), reverse=True)
    margin = best - (ordered[1] if len(ordered) > 1 else 0)
    confidence = min(95, 35 + best * 5 + margin * 3) if best else 20
    return CategoryRecommendation(category, confidence, tuple(sorted(set(matches[category]))))
