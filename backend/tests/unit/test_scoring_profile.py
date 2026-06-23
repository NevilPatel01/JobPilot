from app.jobs.scoring.service import profile_has_scoring_data
from app.models.user import User


def user(*, skills: list[str] | None = None, resume_text: str | None = None) -> User:
    return User(
        oauth_provider="test",
        oauth_id="profile-test",
        email="profile@example.com",
        skills_keywords=skills,
        resume_text=resume_text,
    )


def test_empty_or_contact_only_profile_does_not_enable_scoring() -> None:
    content = {
        "contact": {"full_name": "Example User", "email": "profile@example.com"},
        "experience": [],
        "education": [],
        "projects": [],
        "skills": [],
    }

    assert profile_has_scoring_data(user(), content) is False


def test_skills_enable_personalized_scoring() -> None:
    assert profile_has_scoring_data(user(skills=["Python", "SQL"]), {}) is True


def test_career_history_enables_personalized_scoring() -> None:
    content = {
        "experience": [{"title": "Support Analyst", "company": "Example", "bullets": []}],
        "education": [],
        "projects": [],
        "skills": [],
    }

    assert profile_has_scoring_data(user(), content) is True
