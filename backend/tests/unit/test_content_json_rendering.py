import uuid

from app.models.candidate import CandidateFact
from app.schemas.resume_content import ResumeContent
from app.services.candidate.rendering import render_content_json


def _fact(fact_type: str, payload: dict) -> CandidateFact:
    return CandidateFact(id=uuid.uuid4(), user_id=uuid.uuid4(), fact_type=fact_type, payload=payload, is_prohibited=False)


def test_render_content_json_produces_valid_resume_content():
    facts = [
        _fact("personal", {"full_name": "Jane Doe"}),
        _fact("contact", {"email": "jane@example.com"}),
        _fact("employment", {"company": "Acme", "title": "Engineer", "start_date": "2020", "end_date": "2022", "bullets": ["Built things"]}),
        _fact("skill", {"category": "Languages", "skills": ["Python"]}),
    ]
    result = render_content_json(facts)
    assert isinstance(result, ResumeContent)
    assert result.contact.full_name == "Jane Doe"
    assert result.contact.email == "jane@example.com"
    assert len(result.experience) == 1
    assert result.experience[0].company == "Acme"
    assert result.skills[0].skills == ["Python"]


def test_render_content_json_excludes_prohibited_facts():
    prohibited = _fact("employment", {"company": "Secret Corp", "title": "X"})
    prohibited.is_prohibited = True
    result = render_content_json([prohibited])
    assert result.experience == []


def test_render_content_json_handles_empty_facts():
    result = render_content_json([])
    assert result.experience == []
    assert result.contact.full_name == ""
