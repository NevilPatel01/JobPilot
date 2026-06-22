from copy import deepcopy

import pytest

from app.jobs.resume_templates import build_category_template, profile_has_substance
from app.models.job_intelligence import InboxJob
from app.models.resume import ResumeDocument


def profile_content() -> dict:
    return {
        "contact": {"full_name": "Alex Example", "email": "alex@example.com", "phone": "", "location": "Toronto"},
        "links": [],
        "summary": "Technical professional supporting business systems and building web tools.",
        "experience": [
            {
                "id": "web-exp",
                "company": "Web Co",
                "title": "Web Developer",
                "location": "Toronto",
                "start_date": "2022",
                "end_date": "2024",
                "bullets": ["Built React interfaces and Python APIs."],
            },
            {
                "id": "support-exp",
                "company": "Support Co",
                "title": "Application Support Analyst",
                "location": "Hamilton",
                "start_date": "2020",
                "end_date": "2022",
                "bullets": ["Resolved SQL incidents through ServiceNow."],
            },
        ],
        "education": [],
        "projects": [
            {"id": "cloud-project", "name": "Azure Lab", "url": "", "bullets": ["Deployed Docker services."]},
            {"id": "support-project", "name": "Ticket Dashboard", "url": "", "bullets": ["Reported incident trends."]},
        ],
        "skills": [
            {"id": "development", "name": "Development", "skills": ["React", "Python"]},
            {"id": "support", "name": "Support", "skills": ["ServiceNow", "SQL"]},
        ],
    }


def test_category_template_only_reorders_existing_profile_content() -> None:
    source = profile_content()
    original = deepcopy(source)

    template, notes = build_category_template(source, "app_support_analyst")

    assert source == original
    assert template["summary"] == original["summary"]
    assert {entry["id"] for entry in template["experience"]} == {"web-exp", "support-exp"}
    assert {bullet for entry in template["experience"] for bullet in entry["bullets"]} == {
        "Built React interfaces and Python APIs.",
        "Resolved SQL incidents through ServiceNow.",
    }
    assert {skill for group in template["skills"] for skill in group["skills"]} == {
        "React", "Python", "ServiceNow", "SQL"
    }
    assert notes["truthfulness"].startswith("Reordered existing profile content only")


def test_application_support_template_promotes_relevant_experience_and_skills() -> None:
    template, notes = build_category_template(profile_content(), "app_support_analyst")

    assert template["experience"][0]["id"] == "support-exp"
    assert template["skills"][0]["id"] == "support"
    assert {skill.casefold() for skill in notes["promoted_skills"]} >= {"servicenow", "sql"}


def test_template_rejects_unknown_category() -> None:
    with pytest.raises(ValueError, match="Unsupported resume category"):
        build_category_template(profile_content(), "made_up")


def test_profile_substance_requires_resume_content() -> None:
    empty = profile_content()
    empty.update({"summary": "", "experience": [], "projects": [], "skills": []})

    assert profile_has_substance(profile_content()) is True
    assert profile_has_substance(empty) is False


def test_resume_and_inbox_models_have_bidirectional_link_columns() -> None:
    resume_fk_targets = {foreign_key.target_fullname for foreign_key in ResumeDocument.__table__.c.inbox_job_id.foreign_keys}
    inbox_fk_targets = {foreign_key.target_fullname for foreign_key in InboxJob.__table__.c.resume_id.foreign_keys}

    assert resume_fk_targets == {"inbox_jobs.id"}
    assert inbox_fk_targets == {"resume_documents.id"}
    assert "why_this_version" in ResumeDocument.__table__.c
