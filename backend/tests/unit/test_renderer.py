from app.services.resume.renderer import render_resume_html, render_resume_latex, _latex_esc


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
