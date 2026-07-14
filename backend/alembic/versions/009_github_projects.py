"""GitHub projects import: candidate_digests table + github_import fact source.

Revision ID: 009_github_projects
Revises: 008_candidate_facts
Create Date: 2026-07-14
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "009_github_projects"
down_revision: Union[str, None] = "008_candidate_facts"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

OLD_FACT_SOURCES = ("user_entered", "resume_upload", "linkedin_import", "inferred")
NEW_FACT_SOURCES = OLD_FACT_SOURCES + ("github_import",)


def _in_clause(values) -> str:
    return "(" + ", ".join(f"'{v}'" for v in values) + ")"


def upgrade() -> None:
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())
    if "users" not in tables:
        return

    if "candidate_facts" in tables:
        op.drop_constraint("ck_candidate_facts_source", "candidate_facts", type_="check")
        op.create_check_constraint(
            "ck_candidate_facts_source", "candidate_facts", f"source IN {_in_clause(NEW_FACT_SOURCES)}"
        )

    if "candidate_digests" not in tables:
        op.create_table(
            "candidate_digests",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "user_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("kind", sa.String(30), nullable=False),
            sa.Column("content_text", sa.Text(), nullable=False, server_default=""),
            sa.Column("source_fact_ids", postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=False, server_default="{}"),
            sa.Column("sync_state_json", postgresql.JSONB(), nullable=False, server_default="{}"),
            sa.Column("token_estimate", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.UniqueConstraint("user_id", "kind", name="uq_candidate_digests_user_kind"),
        )
        op.create_index("ix_candidate_digests_user_id", "candidate_digests", ["user_id"])


def downgrade() -> None:
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())

    if "candidate_digests" in tables:
        op.drop_table("candidate_digests")

    if "candidate_facts" in tables:
        # revert rows first so the tighter constraint can be applied
        op.execute("UPDATE candidate_facts SET source = 'inferred' WHERE source = 'github_import'")
        op.drop_constraint("ck_candidate_facts_source", "candidate_facts", type_="check")
        op.create_check_constraint(
            "ck_candidate_facts_source", "candidate_facts", f"source IN {_in_clause(OLD_FACT_SOURCES)}"
        )
