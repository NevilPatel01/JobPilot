from app.services.resume.renderer import (
    render_resume_html,
    render_resume_latex,
    resolve_export_latex,
    _latex_esc,
)


def test_render_resume_html_contains_name(sample_resume):
    html = render_resume_html(sample_resume)
    assert "Jane Developer" in html
    assert "Senior Software Engineer" in html
    assert "FastAPI" in html
    assert "Technical Skills" in html


def test_render_resume_latex_escapes_special_chars():
    assert r"\&" in _latex_esc("A & B")
    assert r"\_" in _latex_esc("foo_bar")


def test_render_resume_latex_preamble(sample_resume):
    latex = render_resume_latex(sample_resume)
    assert r"\documentclass[letterpaper,10pt]{article}" in latex
    assert r"\usepackage{fontawesome5}" not in latex  # removed — crashes Tectonic on macOS
    assert r"\usepackage{carlito}" not in latex  # removed — digit glyphs extract as garbage
    assert r"\usepackage[default]{lato}" in latex
    assert r"\newcommand{\entryrow}" in latex
    assert r"\titleformat{\section}" in latex


def test_render_resume_latex_contains_sections(sample_resume):
    latex = render_resume_latex(sample_resume)
    assert r"\section{Technical Skills}" in latex
    assert r"\section{Work Experience}" in latex
    assert r"\section{Projects}" in latex
    assert r"\section{Education}" in latex
    assert "Jane Developer" in latex
    assert r"\entryrow{" in latex
    assert r"\item " in latex


def test_render_resume_latex_header_contact(sample_resume):
    latex = render_resume_latex(sample_resume)
    # FA icons removed (crashed Tectonic); contact is now plain hyperlinks
    assert r"\faPhone" not in latex
    assert r"\faEnvelope" not in latex
    assert r"\faGithub" not in latex
    assert "jane@example.com" in latex
    assert r"\href{mailto:jane@example.com}" in latex


def test_render_resume_latex_escapes_in_bullets():
    content = {
        "contact": {"full_name": "Test User"},
        "experience": [
            {
                "title": "Engineer",
                "company": "A & B Corp",
                "location": "",
                "start_date": "2020",
                "end_date": "2021",
                "bullets": ["Improved latency by 50% & reliability"],
            }
        ],
    }
    latex = render_resume_latex(content)
    assert r"A \& B Corp" in latex
    assert r"50\% \& reliability" in latex


def test_resolve_export_latex_uses_stored_source(sample_resume):
    custom = r"\documentclass{article}\begin{document}CUSTOM\end{document}"
    latex = resolve_export_latex(sample_resume, custom)
    assert "CUSTOM" in latex
    assert r"\section{Work Experience}" not in latex


def test_resolve_export_latex_generates_when_empty(sample_resume):
    latex = resolve_export_latex(sample_resume, None)
    assert "Jane Developer" in latex
    assert r"\section{Work Experience}" in latex

    latex_blank = resolve_export_latex(sample_resume, "   ")
    assert r"\section{Work Experience}" in latex_blank


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
