import re
from dataclasses import dataclass, field
from typing import Any

from app.jobs.scoring.categories import CATEGORY_LABELS, recommend_category


SKILL_GLOSSARY = {
    "active directory", "aws", "azure", "bash", "ci/cd", "cisco", "docker", "fastapi", "gcp", "git",
    "graphql", "javascript", "jira", "kubernetes", "linux", "microsoft 365", "mongodb", "mysql", "next.js",
    "node.js", "powershell", "postgresql", "python", "react", "rest api", "servicenow", "sql", "terraform",
    "typescript", "windows",
}
SKILL_ALIASES = {
    "amazon web services": "aws",
    "google cloud platform": "gcp",
    "k8s": "kubernetes",
    "m365": "microsoft 365",
    "nodejs": "node.js",
    "postgres": "postgresql",
    "reactjs": "react",
    "service now": "servicenow",
}
SENIOR_TERMS = {"senior", "lead", "principal", "staff", "manager", "director", "architect"}
CITIZENSHIP_RESTRICTIONS = (
    "canadian citizens only",
    "citizenship required",
    "must be a canadian citizen",
    "permanent residents only",
)


def normalize_skill(value: str) -> str:
    normalized = re.sub(r"\s+", " ", value.strip().casefold())
    normalized = normalized.replace("–", "-")
    return SKILL_ALIASES.get(normalized, normalized)


@dataclass(frozen=True)
class CandidateProfile:
    skills: tuple[str, ...] = ()
    years_experience: float | None = None
    work_authorization: str = "work_permit"
    target_provinces: tuple[str, ...] = ("AB", "BC", "ON", "SK")
    relocation_open: bool = True


@dataclass(frozen=True)
class JobFacts:
    title: str
    company: str
    description: str = ""
    skills: tuple[str, ...] = ()
    requirements: tuple[str, ...] = ()
    province: str | None = None
    country: str | None = "CA"
    remote_type: str = "unknown"
    seniority: str | None = None
    experience_min: int | None = None
    experience_max: int | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    source: str = "manual"
    apply_url: str = ""


@dataclass(frozen=True)
class ScoringResult:
    score: int
    label: str
    signals: dict[str, dict[str, Any]]
    matched_skills: tuple[str, ...]
    missing_skills: tuple[str, ...]
    risk_flags: tuple[str, ...]
    recommended_action: str
    explanation: str
    recommended_category: str
    category_confidence: int


def _job_skills(job: JobFacts) -> set[str]:
    explicit = {normalize_skill(skill) for skill in job.skills if skill.strip()}
    if explicit:
        return explicit
    text = f"{job.title} {job.description} {' '.join(job.requirements)}".casefold()
    return {skill for skill in SKILL_GLOSSARY if skill in text}


def _signal(points: float, maximum: int, detail: str) -> dict[str, Any]:
    return {"points": round(max(0, min(maximum, points)), 1), "max": maximum, "detail": detail}


def _label(score: int, overrides: dict[str, int] | None) -> str:
    thresholds = {"low_max": 39, "stretch_max": 59, "reviewed_max": 74, "recommended_max": 84}
    if overrides:
        thresholds.update({key: int(value) for key, value in overrides.items() if key in thresholds})
    if score <= thresholds["low_max"]:
        return "low"
    if score <= thresholds["stretch_max"]:
        return "stretch"
    if score <= thresholds["reviewed_max"]:
        return "reviewed"
    if score <= thresholds["recommended_max"]:
        return "recommended"
    return "priority"


def score_job(
    job: JobFacts,
    candidate: CandidateProfile,
    *,
    threshold_overrides: dict[str, int] | None = None,
) -> ScoringResult:
    required_skills = _job_skills(job)
    candidate_skills = {normalize_skill(skill) for skill in candidate.skills if skill.strip()}
    matched = required_skills & candidate_skills
    missing = required_skills - candidate_skills
    skill_ratio = len(matched) / len(required_skills) if required_skills else 0.5

    signals: dict[str, dict[str, Any]] = {}
    signals["skill_match"] = _signal(
        25 * skill_ratio,
        25,
        f"Matched {len(matched)} of {len(required_skills)} detected skills" if required_skills else "No explicit skills detected; neutral score",
    )

    minimum = job.experience_min
    years = candidate.years_experience
    if minimum is None or years is None:
        experience_points = 8
        experience_detail = "Experience requirement or profile tenure is not specified"
    elif years >= minimum:
        experience_points = 15 if job.experience_max is None or years <= job.experience_max + 3 else 12
        experience_detail = f"Profile experience ({years:g}y) meets the {minimum}y minimum"
    else:
        gap = minimum - years
        experience_points = max(0, 15 - gap * 5)
        experience_detail = f"Profile experience is {gap:g}y below the stated minimum"
    signals["experience_match"] = _signal(experience_points, 15, experience_detail)

    title_seniority = {term for term in SENIOR_TERMS if term in f"{job.title} {job.seniority or ''}".casefold()}
    senior_only = bool(title_seniority & {"lead", "principal", "staff", "director", "architect"}) or (minimum or 0) >= 8
    seniority_points = 2 if senior_only else 7 if "senior" in title_seniority and (years or 0) < 5 else 10
    signals["seniority_match"] = _signal(
        seniority_points, 10, "Role appears senior-only" if senior_only else "Seniority appears compatible"
    )

    province = (job.province or "").upper()
    target_location = province in candidate.target_provinces
    remote_canada = job.remote_type == "remote" and (job.country in (None, "CA"))
    location_points = 15 if target_location else 13 if remote_canada else 8 if job.country == "CA" else 1
    signals["province_location"] = _signal(
        location_points,
        15,
        "Located in a target province" if target_location else "Remote within Canada" if remote_canada else "Outside configured target provinces",
    )

    if remote_canada:
        remote_points, remote_detail = 10, "Remote Canada role"
    elif target_location and candidate.relocation_open:
        remote_points, remote_detail = 9, "Onsite or hybrid in a target province; relocation is enabled"
    elif target_location:
        remote_points, remote_detail = 6, "Target province, but relocation is disabled"
    else:
        remote_points, remote_detail = 4, "Work arrangement has limited alignment with preferences"
    signals["remote_eligibility"] = _signal(remote_points, 10, remote_detail)

    category = recommend_category(job.title, job.description, list(job.skills))
    pr_points = 10 if target_location and category.confidence >= 50 else 8 if remote_canada else 5
    signals["pr_usefulness"] = _signal(
        pr_points,
        10,
        "Technical role in a configured PR-strategy province" if pr_points == 10 else "General Canadian eligibility signal",
    )

    quality_points = 2
    quality_points += 3 if len(job.description) >= 800 else 2 if len(job.description) >= 300 else 0
    quality_points += 2 if job.salary_min or job.salary_max else 0
    quality_points += 2 if job.source not in {"manual", "custom"} else 1
    quality_points += 1 if job.company.strip() else 0
    signals["job_quality"] = _signal(quality_points, 10, "Based on description completeness, compensation, and source")

    friction_points = 1 if any(host in job.apply_url.casefold() for host in ("workday", "taleo", "successfactors")) else 3
    signals["application_friction"] = _signal(
        friction_points, 3, "Likely multi-step ATS portal" if friction_points == 1 else "No high-friction ATS signal detected"
    )
    custom_points = 2 if category.confidence >= 55 else 1
    signals["resume_customizability"] = _signal(
        custom_points, 2, f"Best resume category: {CATEGORY_LABELS[category.category]}"
    )

    restrictions = any(phrase in job.description.casefold() for phrase in CITIZENSHIP_RESTRICTIONS)
    risks: list[str] = []
    if senior_only:
        risks.append("senior_only")
    if job.country not in (None, "CA") or restrictions:
        risks.append("non_canada_eligible")
    if minimum is not None and years is not None and minimum > years + 3:
        risks.append("unrealistic_experience")
    if required_skills and skill_ratio < 0.3:
        risks.append("low_skill_match")

    raw_score = round(sum(float(signal["points"]) for signal in signals.values()))
    if "non_canada_eligible" in risks:
        raw_score = min(raw_score, 35)
    if "senior_only" in risks:
        raw_score = min(raw_score, 55)
    if "unrealistic_experience" in risks or "low_skill_match" in risks:
        raw_score = min(raw_score, 59)
    final_score = max(0, min(100, raw_score))
    label = _label(final_score, threshold_overrides)
    actions = {
        "low": "Archive unless there is a strong personal reason",
        "stretch": "Review gaps before investing in an application",
        "reviewed": "Review and shortlist if the role is still appealing",
        "recommended": "Shortlist and tailor a resume",
        "priority": "Prioritize this application today",
    }
    positives = sorted(signals, key=lambda key: signals[key]["points"] / signals[key]["max"], reverse=True)[:2]
    explanation = (
        f"Strongest signals: {signals[positives[0]]['detail']}; {signals[positives[1]]['detail']}."
        + (f" Review flags: {', '.join(flag.replace('_', ' ') for flag in risks)}." if risks else " No hard risk flags detected.")
    )
    return ScoringResult(
        score=final_score,
        label=label,
        signals=signals,
        matched_skills=tuple(sorted(matched)),
        missing_skills=tuple(sorted(missing)),
        risk_flags=tuple(risks),
        recommended_action=actions[label],
        explanation=explanation,
        recommended_category=category.category,
        category_confidence=category.confidence,
    )
