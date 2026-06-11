import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_resume() -> dict:
    return json.loads((FIXTURES / "sample_resume.json").read_text())


@pytest.fixture
def sample_jd() -> str:
    return (FIXTURES / "sample_jd.txt").read_text()


@pytest.fixture
def sample_jd_analysis() -> dict:
    return {
        "required_skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "Kubernetes"],
        "keywords": ["Python", "FastAPI", "REST API", "async", "microservices"],
        "responsibilities": ["Build backend services", "Write tests"],
        "seniority": "Senior",
    }
