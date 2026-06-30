"""Re-exports all public renderer symbols for backward compatibility."""

from app.services.resume.html import render_cover_letter_html, render_resume_html
from app.services.resume.latex import (
    _latex_esc,
    render_cover_letter_latex,
    render_resume_latex,
    resolve_export_latex,
)
from app.services.resume.pdf_parser import (
    PdfParseResult,
    _parse_pdf_stub,
    compute_section_counts,
    parse_pdf_text,
)

__all__ = [
    "render_resume_html",
    "render_cover_letter_html",
    "render_resume_latex",
    "render_cover_letter_latex",
    "resolve_export_latex",
    "_latex_esc",
    "PdfParseResult",
    "compute_section_counts",
    "parse_pdf_text",
    "_parse_pdf_stub",
]
