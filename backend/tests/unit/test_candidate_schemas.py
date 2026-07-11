import pytest
from pydantic import ValidationError

from app.schemas.candidate import AnswerBankEntryCreate, CandidateFactCreate


def test_candidate_fact_create_rejects_oversized_payload():
    with pytest.raises(ValidationError):
        CandidateFactCreate(fact_type="skill", payload={f"k{i}": i for i in range(51)})


def test_candidate_fact_create_accepts_valid_payload():
    fact = CandidateFactCreate(fact_type="skill", payload={"name": "Python"})
    assert fact.source == "user_entered"
    assert fact.is_prohibited is False


def test_answer_bank_entry_is_sensitive_for_salary_category():
    entry = AnswerBankEntryCreate(question_text="What is your expected salary?", question_category="salary")
    assert entry.is_sensitive is True


def test_answer_bank_entry_is_not_sensitive_for_behavioral_category():
    entry = AnswerBankEntryCreate(question_text="Tell me about a challenge", question_category="behavioral")
    assert entry.is_sensitive is False
