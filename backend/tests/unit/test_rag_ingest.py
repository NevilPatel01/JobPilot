import pytest

from app.services.rag.ingest import _keyword_score, _query_terms


def test_query_terms_extracts_keywords():
    terms = _query_terms("Senior Python Engineer with FastAPI and PostgreSQL")
    assert "python" in terms
    assert "fastapi" in terms


def test_keyword_score_ranks_relevant_chunks():
    terms = _query_terms("python fastapi")
    high = _keyword_score("Built APIs with Python and FastAPI for years", terms)
    low = _keyword_score("Managed retail inventory spreadsheets", terms)
    assert high > low
