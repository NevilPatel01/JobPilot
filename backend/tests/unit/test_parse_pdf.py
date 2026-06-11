import pytest

from app.services.resume.renderer import (
    PdfParseResult,
    _parse_pdf_stub,
    compute_section_counts,
    parse_pdf_text,
)


def test_compute_section_counts(sample_resume):
    counts = compute_section_counts(sample_resume)
    assert counts["experience"] == 1
    assert counts["education"] == 1
    assert counts["has_contact_name"] == 1
    assert counts["has_summary"] == 1


def test_parse_pdf_stub_extracts_summary():
    result = _parse_pdf_stub("Jane Developer\nSenior engineer with Python experience.")
    assert isinstance(result, PdfParseResult)
    assert "Jane Developer" in result.content["summary"]
    assert result.confidence == 0.25
    assert result.section_counts["experience"] == 0
    assert any("No API key" in w for w in result.warnings)


def test_parse_pdf_stub_empty_text():
    result = _parse_pdf_stub("")
    assert result.confidence == 0.0
    assert any("Could not extract" in w for w in result.warnings)


@pytest.mark.asyncio
async def test_parse_pdf_text_without_llm_uses_stub():
    result = await parse_pdf_text("Some resume text here.", None)
    assert result.content["summary"].startswith("Some resume text")
    assert result.confidence <= 0.3


@pytest.mark.asyncio
async def test_parse_pdf_text_empty_without_llm():
    result = await parse_pdf_text("   ", None)
    assert result.confidence == 0.0
