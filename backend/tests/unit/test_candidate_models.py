from app.models.candidate import (
    ANSWER_CATEGORIES, FACT_SOURCES, FACT_TYPES, VERIFICATION_STATUSES,
    Achievement, AnswerBankEntry, CandidateFact, CareerProfile,
)


def test_candidate_fact_table_has_user_id_fk():
    fk_targets = {fk.target_fullname for fk in CandidateFact.__table__.foreign_keys}
    assert "users.id" in fk_targets


def test_candidate_fact_constraints_reference_constants():
    names = {c.name for c in CandidateFact.__table__.constraints}
    assert {"ck_candidate_facts_fact_type", "ck_candidate_facts_source", "ck_candidate_facts_verification_status"} <= names


def test_achievement_related_fact_id_is_set_null_not_cascade():
    fk = next(fk for fk in Achievement.__table__.foreign_keys if fk.column.table.name == "candidate_facts")
    assert fk.ondelete == "SET NULL"


def test_career_profile_has_user_id_fk():
    fk_targets = {fk.target_fullname for fk in CareerProfile.__table__.foreign_keys}
    assert "users.id" in fk_targets


def test_answer_bank_category_constraint_matches_constant():
    constraint = next(c for c in AnswerBankEntry.__table__.constraints if c.name == "ck_answer_bank_category")
    text = str(constraint.sqltext)
    for cat in ANSWER_CATEGORIES:
        assert f"'{cat}'" in text
