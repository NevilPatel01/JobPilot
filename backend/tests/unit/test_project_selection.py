from app.services.candidate.project_selection import classify_job_seniority, select_projects


def _project(name, tech, *, pinned=False, stars=0):
    return {
        "fact_id": f"id-{name}", "name": name, "tech_stack": tech,
        "pinned": pinned, "stars": stars, "url": "", "one_liner": "", "highlights": [],
    }


PROJECTS = [
    _project("cloud-tool", ["aws", "terraform"], stars=10),
    _project("py-app", ["python", "fastapi"], stars=5),
    _project("misc", ["arduino"], stars=1),
]


def test_classify_job_seniority():
    assert classify_job_seniority("Junior Developer", None) == "junior"
    assert classify_job_seniority("Software Engineer Intern", None) == "junior"
    assert classify_job_seniority("Senior Platform Engineer", None) == "senior"
    assert classify_job_seniority("Staff Engineer", "lead") == "senior"
    assert classify_job_seniority("Software Developer", None) == "mid"


def test_junior_roles_get_up_to_two_relevant_projects():
    selected = select_projects(PROJECTS, job_skills=["python", "aws"], seniority="junior", experience_count=1)
    assert [p["name"] for p in selected] == ["cloud-tool", "py-app"]


def test_mid_roles_only_get_projects_covering_job_skills():
    selected = select_projects(PROJECTS, job_skills=["arduino"], seniority="mid", experience_count=3)
    assert [p["name"] for p in selected] == ["misc"]
    # no overlap at all → no projects for mid
    assert select_projects(PROJECTS, job_skills=["cobol"], seniority="mid", experience_count=3) == []


def test_senior_roles_get_at_most_one_project():
    selected = select_projects(PROJECTS, job_skills=["python", "aws", "terraform"], seniority="senior", experience_count=4)
    assert len(selected) <= 1


def test_senior_with_no_relevant_projects_gets_none():
    assert select_projects(PROJECTS, job_skills=["cobol"], seniority="senior", experience_count=4) == []


def test_career_changer_override_treats_thin_experience_as_junior():
    selected = select_projects(PROJECTS, job_skills=["python", "aws"], seniority="senior", experience_count=1)
    assert len(selected) == 2  # junior rule applies despite senior JD


def test_pinned_projects_rank_first_within_relevance_ties():
    projects = [
        _project("a", ["python"], stars=100),
        _project("b", ["python"], pinned=True, stars=0),
    ]
    selected = select_projects(projects, job_skills=["python"], seniority="junior", experience_count=0)
    assert selected[0]["name"] == "b"
