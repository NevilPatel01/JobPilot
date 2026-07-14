"""Seniority-adaptive project selection for tailored resumes (deterministic).

Rules (PHASE_1_IMPLEMENTATION_SPEC §Project selection):
- junior/intern roles: up to 2 relevant projects
- mid: 1–2, only projects that cover a job skill
- senior+: 0–1, only if directly relevant — experience carries senior resumes
- career-changer override: fewer than 2 employment entries → junior rule
"""

SENIOR_TERMS = ("senior", "lead", "principal", "staff", "manager", "director", "architect")
JUNIOR_TERMS = ("junior", "intern", "entry", "co-op", "coop", "graduate", "associate")

_COUNTS = {"junior": 2, "mid": 2, "senior": 1}


def _norm(value: str) -> str:
    return (value or "").strip().casefold()


def classify_job_seniority(job_title: str | None, job_seniority: str | None) -> str:
    text = f"{_norm(job_title or '')} {_norm(job_seniority or '')}"
    if any(term in text for term in JUNIOR_TERMS):
        return "junior"
    if any(term in text for term in SENIOR_TERMS):
        return "senior"
    return "mid"


def _overlap(project: dict, job_skills: set[str]) -> int:
    tech = {_norm(t) for t in project.get("tech_stack") or []}
    return len(tech & job_skills)


def select_projects(
    projects: list[dict],
    *,
    job_skills: list[str],
    seniority: str,
    experience_count: int,
) -> list[dict]:
    if experience_count < 2:
        seniority = "junior"  # career-changer / early-career override
    normalized_skills = {_norm(s) for s in job_skills if _norm(s)}

    ranked = sorted(
        projects,
        key=lambda p: (
            -_overlap(p, normalized_skills),
            not p.get("pinned"),
            -int(p.get("stars") or 0),
            _norm(p.get("name") or ""),
        ),
    )
    if seniority == "junior":
        # relevance-first, but a junior resume may still show top projects with no overlap
        selected = ranked
    else:
        # mid/senior: a project must actually cover a job skill to earn its space
        selected = [p for p in ranked if _overlap(p, normalized_skills) > 0]
    return selected[: _COUNTS[seniority]]
