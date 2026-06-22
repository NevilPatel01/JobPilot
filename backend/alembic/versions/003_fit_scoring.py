"""Persist explainable per-user job fit scores.

Revision ID: 003_fit_scoring
Revises: 002_job_intelligence
Create Date: 2026-06-21
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "003_fit_scoring"
down_revision: Union[str, None] = "002_job_intelligence"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if not {"users", "jobs", "inbox_jobs"}.issubset(tables):
        return

    if "job_fit_scores" not in tables:
        op.create_table(
            "job_fit_scores",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("score", sa.Integer(), nullable=False),
            sa.Column("label", sa.String(40), nullable=False),
            sa.Column("signals", postgresql.JSONB(), nullable=False),
            sa.Column("matched_skills", postgresql.ARRAY(sa.String()), nullable=False),
            sa.Column("missing_skills", postgresql.ARRAY(sa.String()), nullable=False),
            sa.Column("risk_flags", postgresql.ARRAY(sa.String()), nullable=False),
            sa.Column("recommended_action", sa.String(120), nullable=False),
            sa.Column("explanation", sa.Text(), nullable=False),
            sa.Column("recommended_category", sa.String(50)),
            sa.Column("category_confidence", sa.Integer()),
            sa.Column("scored_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.UniqueConstraint("user_id", "job_id", name="uq_job_fit_scores_user_job"),
        )
        op.create_index("ix_job_fit_scores_user_id", "job_fit_scores", ["user_id"])
        op.create_index("ix_job_fit_scores_job_id", "job_fit_scores", ["job_id"])
        op.create_index("ix_job_fit_scores_score", "job_fit_scores", ["score"])
        op.create_index("ix_job_fit_scores_label", "job_fit_scores", ["label"])

    columns = {column["name"] for column in sa.inspect(bind).get_columns("inbox_jobs")}
    if "fit_score_id" not in columns:
        op.add_column(
            "inbox_jobs",
            sa.Column(
                "fit_score_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("job_fit_scores.id", ondelete="SET NULL"),
                nullable=True,
            ),
        )
        op.create_unique_constraint("uq_inbox_jobs_fit_score_id", "inbox_jobs", ["fit_score_id"])


def downgrade() -> None:
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())
    if "inbox_jobs" in tables:
        columns = {column["name"] for column in sa.inspect(bind).get_columns("inbox_jobs")}
        if "fit_score_id" in columns:
            op.drop_constraint("uq_inbox_jobs_fit_score_id", "inbox_jobs", type_="unique")
            op.drop_column("inbox_jobs", "fit_score_id")
    if "job_fit_scores" in tables:
        op.drop_table("job_fit_scores")
