from app.jobs.pipeline.normalizer import (
    build_dedupe_hash,
    canonicalize_url,
    normalize_job,
)


def test_canonicalize_url_removes_tracking_and_normalizes_host() -> None:
    result = canonicalize_url(
        "http://WWW.Example.com/jobs/123/?utm_source=linkedin&department=it&ref=feed#apply"
    )

    assert result == "https://example.com/jobs/123?department=it"


def test_normalize_job_extracts_canadian_location_and_remote_type() -> None:
    job = normalize_job(
        {
            "title": "  Application   Support Analyst ",
            "company": "Example Corp",
            "location": "Calgary, Alberta (Hybrid)",
            "url": "https://example.com/jobs/analyst",
            "skills": ["SQL", " sql ", "ServiceNow"],
        }
    )

    assert job.title == "Application Support Analyst"
    assert job.province == "AB"
    assert job.city == "Calgary"
    assert job.remote_type == "hybrid"
    assert job.skills == ["SQL", "ServiceNow"]
    assert len(job.dedupe_hash) == 64


def test_dedupe_hash_ignores_case_and_punctuation_but_includes_city() -> None:
    hamilton = build_dedupe_hash("IT Support — Level 1", "ACME, Inc.", "Hamilton")
    same = build_dedupe_hash("it support level 1", "Acme Inc", "HAMILTON")
    calgary = build_dedupe_hash("it support level 1", "Acme Inc", "Calgary")

    assert hamilton == same
    assert hamilton != calgary
