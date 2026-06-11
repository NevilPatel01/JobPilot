from app.schemas.resume_content import ResumeContent, empty_resume_content, resume_to_text


def test_empty_resume_content_defaults():
    content = empty_resume_content()
    assert content.contact.full_name == ""
    assert content.experience == []
    assert content.skills == []


def test_resume_to_text_includes_sections(sample_resume):
    text = resume_to_text(ResumeContent.model_validate(sample_resume))
    assert "Jane Developer" in text
    assert "FastAPI" in text
    assert "Acme Corp" in text
    assert "University of Toronto" in text
    assert "Python" in text


def test_resume_content_validates_nested_structure(sample_resume):
    content = ResumeContent.model_validate(sample_resume)
    assert len(content.experience) == 1
    assert content.experience[0].bullets[0].startswith("Built FastAPI")
