from app.services.cover_letter.generator import enforce_word_limits, parse_cover_letter_response, word_count


def test_word_count_sums_paragraphs():
    assert word_count(["Hello world", "One two three"]) == 5


def test_enforce_word_limits_trims_long_letter():
    long_para = " ".join(["word"] * 300)
    short_para = " ".join(["brief"] * 50)
    result = enforce_word_limits([long_para, short_para], max_words=400)
    assert word_count(result) <= 400
    assert len(result) >= 1


def test_enforce_word_limits_keeps_short_letter():
    paras = ["Short opening.", "Middle with a few more words here.", "Closing thoughts."]
    assert enforce_word_limits(paras) == paras


def test_parse_cover_letter_response_normalizes():
    paragraphs, closing = parse_cover_letter_response(
        {"paragraphs": ["  First para.  ", "", "Second para."], "closing": "Best regards,"}
    )
    assert paragraphs == ["First para.", "Second para."]
    assert closing == "Best regards,"


def test_build_cover_letter_prompt_includes_context():
    from app.services.cover_letter.generator import build_cover_letter_prompt

    prompt = build_cover_letter_prompt(
        meta={"hiring_manager_name": "Jane", "additional_context": "Referral from Bob"},
        company={"company_name": "Acme", "summary": "Leading fintech"},
        jd_analysis={"role_title": "Engineer", "keywords": ["Python"]},
        job_description="Build APIs",
        resume_text="Built FastAPI services",
    )
    assert "Jane" in prompt
    assert "Acme" in prompt
    assert "250-400" in prompt
    assert "Referral from Bob" in prompt
