from app.services.evidence.guard import extract_guard_context, guard_proposed_change


def test_extract_guard_context_collects_companies_and_numbers(sample_resume):
    ctx = extract_guard_context(sample_resume)
    assert ctx["allowed_company_names"]  # non-empty, derived from sample_resume fixture
    assert isinstance(ctx["allowed_numbers"], set)


def test_guard_proposed_change_allows_value_matching_existing_company(sample_resume):
    ctx = extract_guard_context(sample_resume)
    real_company = sample_resume["experience"][0]["company"]
    value, warning = guard_proposed_change("experience[0].company", real_company, **ctx)
    assert value == real_company
    assert warning is None


def test_guard_proposed_change_rejects_invented_company(sample_resume):
    ctx = extract_guard_context(sample_resume)
    value, warning = guard_proposed_change("experience[0].company", "Totally Fake Corp", **ctx)
    assert value != "Totally Fake Corp"
    assert warning is not None
    assert "Fake Corp" in warning or "invented" in warning.lower()


def test_guard_proposed_change_rejects_invented_number_in_bullet(sample_resume):
    ctx = extract_guard_context(sample_resume)
    value, warning = guard_proposed_change(
        "experience[0].bullets[0]", "Increased revenue by 9999%", **ctx
    )
    assert "9999" not in str(value)
    assert warning is not None


def test_guard_proposed_change_allows_skills_freely(sample_resume):
    ctx = extract_guard_context(sample_resume)
    value, warning = guard_proposed_change("skills[0].skills", ["Python", "Rust", "WebAssembly"], **ctx)
    assert value == ["Python", "Rust", "WebAssembly"]
    assert warning is None
