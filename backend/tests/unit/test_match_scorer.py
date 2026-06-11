from app.services.match_scorer import extract_skills, tfidf_score, tokenize


def test_tokenize_lowercases_and_splits():
    tokens = tokenize("Python 3.11, FastAPI & PostgreSQL")
    assert "python" in tokens
    assert "fastapi" in tokens
    assert "postgresql" in tokens


def test_tfidf_score_finds_overlap(sample_resume, sample_jd):
    from app.schemas.resume_content import ResumeContent, resume_to_text

    text = resume_to_text(ResumeContent.model_validate(sample_resume))
    result = tfidf_score(text, sample_jd)
    assert result["score"] > 0
    assert "python" in result["matched_keywords"] or "fastapi" in result["matched_keywords"]


def test_extract_skills_filters_stopwords():
    skills = extract_skills("Python and FastAPI for the backend with PostgreSQL")
    assert "python" in skills
    assert "and" not in skills
