import json

from app.jobs.sources.adzuna import AdzunaSource
from app.jobs.sources.job_bank import JobBankSource
from app.jobs.sources.jsearch import JSearchSource
from app.jobs.sources.job_bank import JobBankSource
from app.services.scraper_runner import ROLE_PRIORITY, build_query_queue
from tests.conftest import FIXTURES


def load_json(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def test_adzuna_fixture_normalizes_to_target_province() -> None:
    job = AdzunaSource.parse_item(load_json("adzuna_job.json"), "Toronto")

    assert job is not None
    assert job.source == "adzuna"
    assert job.province == "ON"
    assert job.city == "Toronto"
    assert job.remote_type == "hybrid"
    assert job.currency == "CAD"
    assert "utm_source" not in job.canonical_url


def test_jsearch_fixture_normalizes_hourly_salary_and_remote_status() -> None:
    job = JSearchSource.parse_item(load_json("jsearch_job.json"), "Calgary")

    assert job is not None
    assert job.province == "AB"
    assert job.remote_type == "remote"
    assert job.salary_min == 66560
    assert job.salary_max == 83200
    assert job.posted_date.isoformat() == "2026-06-19"


def test_jsearch_rejects_non_canadian_result() -> None:
    data = {**load_json("jsearch_job.json"), "job_country": "US"}

    assert JSearchSource.parse_item(data, "Calgary") is None


def test_job_bank_fixture_parses_listing_and_annualizes_salary() -> None:
    html = (FIXTURES / "job_bank_search.html").read_text()
    jobs = JobBankSource.parse_search_html(html, "Regina")

    assert len(jobs) == 1
    job = jobs[0]
    assert job.source == "job_bank"
    assert job.province == "SK"
    assert job.city == "Regina"
    assert job.salary_min == 58240
    assert job.salary_max == 70720
    assert job.source_job_id == "445566"


def test_job_bank_salary_rejects_unlabelled_hourly_values() -> None:
    assert JobBankSource.parse_salary("$25 to $35") == (None, None)


def test_query_queue_prioritizes_top_three_roles_across_target_regions() -> None:
    queue = build_query_queue(12)

    assert len(queue) == 12
    assert {query for query, _ in queue} == set(ROLE_PRIORITY[:3])
    assert {city for _, city in queue} == {"Hamilton", "Calgary", "Regina", "Vancouver"}


def test_keyed_sources_report_missing_credentials(monkeypatch) -> None:
    from app.core.config import settings

    monkeypatch.setattr(settings, "adzuna_app_id", "")
    monkeypatch.setattr(settings, "adzuna_app_key", "")
    monkeypatch.setattr(settings, "rapidapi_key", "")

    assert AdzunaSource().credential_status == "missing"
    assert JSearchSource().credential_status == "missing"
    assert JobBankSource().credential_status == "not_required"
