import pytest
from pydantic import ValidationError

from app.api.schemas import UserScoringPrefsUpdate
from app.jobs.scoring.engine import CandidateProfile, JobFacts, score_job


def strong_candidate() -> CandidateProfile:
    return CandidateProfile(
        skills=("Python", "SQL", "Docker", "Azure", "ServiceNow"),
        years_experience=5,
        work_authorization="work_permit",
        target_provinces=("AB", "BC", "ON", "SK"),
        relocation_open=True,
    )


def test_strong_target_province_match_is_priority() -> None:
    result = score_job(
        JobFacts(
            title="Application Support Analyst",
            company="Example",
            description="Support production applications and resolve incidents using SQL and ServiceNow.",
            skills=("SQL", "ServiceNow", "Python"),
            province="ON",
            remote_type="hybrid",
            experience_min=3,
            salary_min=75000,
            source="job_bank",
            apply_url="https://example.com/apply",
        ),
        strong_candidate(),
    )

    assert result.score >= 85
    assert result.label == "priority"
    assert result.risk_flags == ()
    assert result.recommended_category == "app_support_analyst"
    assert set(result.matched_skills) == {"python", "servicenow", "sql"}


def test_low_skill_match_is_flagged_and_capped_below_reviewed() -> None:
    result = score_job(
        JobFacts(
            title="Cloud Platform Engineer",
            company="Example",
            skills=("AWS", "Kubernetes", "Terraform", "Linux"),
            province="AB",
            remote_type="hybrid",
            experience_min=3,
        ),
        CandidateProfile(skills=("Excel",), years_experience=4),
    )

    assert "low_skill_match" in result.risk_flags
    assert result.score <= 59
    assert set(result.missing_skills) == {"aws", "kubernetes", "linux", "terraform"}


def test_senior_only_role_is_flagged_and_capped() -> None:
    result = score_job(
        JobFacts(
            title="Principal Cloud Architect",
            company="Example",
            skills=("Azure",),
            province="BC",
            experience_min=10,
        ),
        strong_candidate(),
    )

    assert "senior_only" in result.risk_flags
    assert "unrealistic_experience" in result.risk_flags
    assert result.score <= 55


def test_citizenship_restriction_is_non_canada_eligible_for_work_permit() -> None:
    result = score_job(
        JobFacts(
            title="IT Support Technician",
            company="Example",
            description="Canadian citizens only. Provide technical support for Windows users.",
            skills=("Windows",),
            province="SK",
        ),
        strong_candidate(),
    )

    assert "non_canada_eligible" in result.risk_flags
    assert result.score <= 35


def test_custom_thresholds_change_label_without_changing_score() -> None:
    job = JobFacts(
        title="Application Support Analyst",
        company="Example",
        skills=("SQL", "ServiceNow"),
        province="ON",
        remote_type="remote",
        experience_min=2,
        salary_min=70000,
        source="job_bank",
    )
    default = score_job(job, strong_candidate())
    stricter = score_job(job, strong_candidate(), threshold_overrides={"recommended_max": 99})

    assert default.score == stricter.score
    assert default.label == "priority"
    assert stricter.label == "recommended"


def test_no_explicit_skills_gets_neutral_skill_score() -> None:
    result = score_job(
        JobFacts(title="Operations Coordinator", company="Example", province="ON"),
        strong_candidate(),
    )

    assert result.signals["skill_match"]["points"] == 12.5
    assert result.matched_skills == ()
    assert "low_skill_match" not in result.risk_flags


def test_signal_weights_total_one_hundred() -> None:
    result = score_job(JobFacts(title="IT Support", company="Example"), strong_candidate())

    assert sum(signal["max"] for signal in result.signals.values()) == 100


def test_scoring_preferences_reject_unordered_thresholds() -> None:
    with pytest.raises(ValidationError, match="must be ordered"):
        UserScoringPrefsUpdate(
            threshold_overrides={
                "low_max": 60,
                "stretch_max": 50,
                "reviewed_max": 74,
                "recommended_max": 84,
            }
        )


def test_scoring_preferences_accept_partial_threshold_override() -> None:
    prefs = UserScoringPrefsUpdate(threshold_overrides={"recommended_max": 90})

    assert prefs.threshold_overrides == {"recommended_max": 90}
