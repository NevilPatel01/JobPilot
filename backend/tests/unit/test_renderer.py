from app.services.resume.renderer import render_resume_html, render_resume_latex, resolve_export_latex, _latex_esc


def test_render_resume_html_contains_name(sample_resume):
    html = render_resume_html(sample_resume)
    assert "Jane Developer" in html
    assert "Senior Software Engineer" in html
    assert "FastAPI" in html


def test_render_resume_latex_escapes_special_chars():
    assert r"\&" in _latex_esc("A & B")
    assert r"\_" in _latex_esc("foo_bar")


def test_render_resume_latex_contains_sections(sample_resume):
    latex = render_resume_latex(sample_resume)
    assert r"\section*{Experience}" in latex
    assert "Jane Developer" in latex or "Developer" in latex


def test_resolve_export_latex_ignores_stale_source(sample_resume):
    stale = r"\documentclass{article}\begin{document}STALE\end{document}"
    latex = resolve_export_latex(sample_resume, stale)
    assert "STALE" not in latex
    assert "Jane Developer" in latex


def test_render_cover_letter_html(sample_resume):
    from app.services.resume.renderer import render_cover_letter_html, render_cover_letter_latex

    content = {
        "recipient_name": "Jane Smith",
        "company_name": "Acme Corp",
        "company_address": "123 Main St",
        "date": "June 10, 2026",
        "salutation": "Dear Jane Smith,",
        "paragraphs": ["I am excited to apply for the role."],
        "closing": "Sincerely,",
    }
    contact = sample_resume["contact"]
    html = render_cover_letter_html(content, contact)
    assert "Jane Smith" in html
    assert "excited to apply" in html
    latex = render_cover_letter_latex(content, contact)
    assert r"\begin{document}" in latex
    assert "Jane Developer" in latex
