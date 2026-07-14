from app.agents.validation import guard_tailored_content

SOURCE = {
    "contact": {"full_name": "Nevil"},
    "summary": "Support analyst.",
    "experience": [
        {"id": "e1", "company": "Acme", "title": "Analyst", "bullets": ["Resolved tickets"]},
    ],
    "education": [],
    "skills": [{"id": "s1", "name": "Skills", "skills": ["Python"]}],
    "projects": [
        {"id": "p1", "name": "JobPilot", "bullets": ["AI resume builder"], "evidence_fact_id": "fact-1"},
        {"id": "p2", "name": "Orphan", "bullets": ["No evidence"], "evidence_fact_id": ""},
    ],
}


def _tailored(**overrides):
    tailored = {
        **SOURCE,
        "projects": [
            {"id": "p1", "name": "JobPilot", "bullets": ["AI resume builder"], "evidence_fact_id": "fact-1"},
            {"id": "p2", "name": "Orphan", "bullets": ["No evidence"], "evidence_fact_id": ""},
        ],
    }
    tailored.update(overrides)
    return tailored


FACTS_GUARD = {"confirmed_project_fact_ids": ["fact-1"], "prohibited_terms": []}


def test_guard_without_facts_context_behaves_as_before():
    cleaned, warnings = guard_tailored_content(SOURCE, _tailored())
    assert [p["name"] for p in cleaned["projects"]] == ["JobPilot", "Orphan"]


def test_guard_drops_project_without_confirmed_evidence_fact():
    cleaned, warnings = guard_tailored_content(SOURCE, _tailored(), facts_guard=FACTS_GUARD)
    assert [p["name"] for p in cleaned["projects"]] == ["JobPilot"]
    assert any("evidence" in w.lower() or "confirmed" in w.lower() for w in warnings)


def test_guard_drops_project_with_unknown_evidence_fact():
    guard = {"confirmed_project_fact_ids": ["other-fact"], "prohibited_terms": []}
    cleaned, _ = guard_tailored_content(SOURCE, _tailored(), facts_guard=guard)
    assert cleaned["projects"] == []


def test_guard_strips_prohibited_skills():
    guard = {"confirmed_project_fact_ids": ["fact-1"], "prohibited_terms": ["kubernetes"]}
    tailored = _tailored(skills=[{"id": "s1", "name": "Skills", "skills": ["Python", "Kubernetes"]}])
    cleaned, warnings = guard_tailored_content(SOURCE, tailored, facts_guard=guard)
    all_skills = [s for cat in cleaned["skills"] for s in cat["skills"]]
    assert "Kubernetes" not in all_skills
    assert "Python" in all_skills
    assert any("prohibited" in w.lower() for w in warnings)


def test_guard_removes_experience_matching_prohibited_employer():
    guard = {"confirmed_project_fact_ids": ["fact-1"], "prohibited_terms": ["ghost corp"]}
    tailored = _tailored(
        experience=[
            {"id": "e1", "company": "Acme", "title": "Analyst", "bullets": ["Resolved tickets"]},
            {"id": "e9", "company": "Ghost Corp", "title": "CTO", "bullets": ["Ran everything"]},
        ]
    )
    # Ghost Corp is also not in source, so the base guard would drop it anyway;
    # make it present in source to prove the prohibited check alone removes it.
    source = {
        **SOURCE,
        "experience": SOURCE["experience"] + [
            {"id": "e9", "company": "Ghost Corp", "title": "CTO", "bullets": ["Ran everything"]}
        ],
    }
    cleaned, warnings = guard_tailored_content(source, tailored, facts_guard=guard)
    assert [e["company"] for e in cleaned["experience"]] == ["Acme"]
