"""Candidate evidence: candidate_facts, achievements, career_profiles, answer_bank_entries.

Revision ID: 008_candidate_facts
Revises: 007_audit_and_provenance
Create Date: 2026-07-10
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "008_candidate_facts"
down_revision: Union[str, None] = "007_audit_and_provenance"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

FACT_TYPES = (
    "personal", "contact", "work_authorization", "location", "target_role",
    "target_industry", "employment", "education", "certification",
    "project", "skill", "achievement", "metric",
)
FACT_SOURCES = ("user_entered", "resume_upload", "linkedin_import", "inferred")
VERIFICATION_STATUSES = ("unverified", "user_confirmed", "contradicted")
ANSWER_CATEGORIES = (
    "behavioral", "logistics", "salary", "work_authorization",
    "demographic", "legal_declaration", "other",
)


def _in_clause(values) -> str:
    return "(" + ", ".join(f"'{v}'" for v in values) + ")"


def upgrade() -> None:
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())
    if "users" not in tables:
        return

    if "candidate_facts" not in tables:
        op.create_table(
            "candidate_facts",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("fact_type", sa.String(30), nullable=False),
            sa.Column("payload", postgresql.JSONB(), nullable=False, server_default="{}"),
            sa.Column("source", sa.String(30), nullable=False, server_default="user_entered"),
            sa.Column("verification_status", sa.String(20), nullable=False, server_default="unverified"),
            sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
            sa.Column("superseded_by_id", postgresql.UUID(as_uuid=True)),
            sa.Column("is_prohibited", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.CheckConstraint(f"fact_type IN {_in_clause(FACT_TYPES)}", name="ck_candidate_facts_fact_type"),
            sa.CheckConstraint(f"source IN {_in_clause(FACT_SOURCES)}", name="ck_candidate_facts_source"),
            sa.CheckConstraint(
                f"verification_status IN {_in_clause(VERIFICATION_STATUSES)}",
                name="ck_candidate_facts_verification_status",
            ),
        )
        op.create_foreign_key(
            "fk_candidate_facts_superseded_by", "candidate_facts", "candidate_facts",
            ["superseded_by_id"], ["id"], ondelete="SET NULL",
        )
        op.create_index("ix_candidate_facts_user_id", "candidate_facts", ["user_id"])
        op.create_index("ix_candidate_facts_user_type", "candidate_facts", ["user_id", "fact_type"])

    if "achievements" not in tables:
        op.create_table(
            "achievements",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("related_fact_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("candidate_facts.id", ondelete="SET NULL")),
            sa.Column("situation", sa.Text(), nullable=False, server_default=""),
            sa.Column("task", sa.Text(), nullable=False, server_default=""),
            sa.Column("action", sa.Text(), nullable=False, server_default=""),
            sa.Column("result", sa.Text(), nullable=False, server_default=""),
            sa.Column("metrics", postgresql.JSONB(), nullable=False, server_default="{}"),
            sa.Column("tags", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"),
            sa.Column("verification_status", sa.String(20), nullable=False, server_default="unverified"),
            sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
            sa.Column("source", sa.String(30), nullable=False, server_default="user_entered"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_achievements_user_id", "achievements", ["user_id"])

    if "career_profiles" not in tables:
        op.create_table(
            "career_profiles",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("name", sa.String(100), nullable=False),
            sa.Column("description", sa.Text(), nullable=False, server_default=""),
            sa.Column("emphasis_fact_ids", postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=False, server_default="{}"),
            sa.Column("positioning_statement", sa.Text(), nullable=False, server_default=""),
            sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_career_profiles_user_id", "career_profiles", ["user_id"])

    if "answer_bank_entries" not in tables:
        op.create_table(
            "answer_bank_entries",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("question_text", sa.Text(), nullable=False),
            sa.Column("question_category", sa.String(30), nullable=False),
            sa.Column("answer_text", sa.Text(), nullable=False, server_default=""),
            sa.Column("is_sensitive", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("related_fact_ids", postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=False, server_default="{}"),
            sa.Column("last_used_at", sa.DateTime(timezone=True)),
            sa.Column("usage_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.CheckConstraint(f"question_category IN {_in_clause(ANSWER_CATEGORIES)}", name="ck_answer_bank_category"),
        )
        op.create_index("ix_answer_bank_entries_user_id", "answer_bank_entries", ["user_id"])


def downgrade() -> None:
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())
    for table in ("answer_bank_entries", "career_profiles", "achievements", "candidate_facts"):
        if table in tables:
            op.drop_table(table)
