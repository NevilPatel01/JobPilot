from app.services.ats.scorer import score_resume


def test_score_resume_strong_match(sample_resume, sample_jd, sample_jd_analysis):
    result = score_resume(sample_resume, sample_jd, sample_jd_analysis)
    assert result.overall_score >= 60
    assert result.keyword_match >= 40
    assert "Python" in result.matched_keywords
    assert result.semantic_score > 0
    assert result.section_score >= 80


def test_score_resume_missing_skills_lower_score(sample_resume, sample_jd):
    jd_analysis = {
        "required_skills": ["Rust", "Haskell", "COBOL"],
        "keywords": ["Rust", "Haskell"],
    }
    result = score_resume(sample_resume, sample_jd, jd_analysis)
    assert "Rust" in result.missing_keywords
    assert result.skills_coverage < 50
    assert any("missing" in s.lower() or "skills" in s.lower() for s in result.suggestions)


def test_score_resume_empty_content_penalized(sample_jd):
    from app.schemas.resume_content import empty_resume_content

    result = score_resume(empty_resume_content().model_dump(), sample_jd, {"keywords": ["Python"]})
    assert result.overall_score < 60
    assert result.section_score < 50


def test_score_resume_to_dict_keys(sample_resume, sample_jd, sample_jd_analysis):
    d = score_resume(sample_resume, sample_jd, sample_jd_analysis).to_dict()
    assert "breakdown" in d
    assert "matched_keywords" in d
    assert "semantic_score" in d
