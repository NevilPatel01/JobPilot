"""Job intelligence inbox and normalized job fields.

Revision ID: 002_job_intelligence
Revises: 001_resume_agents
Create Date: 2026-06-21
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "002_job_intelligence"
down_revision: Union[str, None] = "001_resume_agents"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


JOB_COLUMNS = (
    sa.Column("province", sa.String(2), nullable=True),
    sa.Column("city", sa.String(120), nullable=True),
    sa.Column("remote_type", sa.String(20), nullable=True),
    sa.Column("job_type", sa.String(50), nullable=True),
    sa.Column("requirements", postgresql.JSONB(), nullable=True),
    sa.Column("skills", postgresql.ARRAY(sa.String()), nullable=True),
    sa.Column("seniority", sa.String(50), nullable=True),
    sa.Column("experience_min", sa.Integer(), nullable=True),
    sa.Column("experience_max", sa.Integer(), nullable=True),
    sa.Column("apply_url", sa.Text(), nullable=True),
    sa.Column("canonical_url", sa.Text(), nullable=True),
    sa.Column("canonical_job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True),
    sa.Column("posted_date", sa.Date(), nullable=True),
    sa.Column("closing_date", sa.Date(), nullable=True),
    sa.Column("raw_payload", postgresql.JSONB(), nullable=True),
)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    # Fresh installs are created from current metadata immediately after Alembic.
    if "jobs" not in tables or "users" not in tables or "user_applications" not in tables:
        return

    existing_columns = {column["name"] for column in inspector.get_columns("jobs")}
    for column in JOB_COLUMNS:
        if column.name not in existing_columns:
            op.add_column("jobs", column)

    op.execute("CREATE INDEX IF NOT EXISTS ix_jobs_province ON jobs (province)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_jobs_canonical_url ON jobs (canonical_url)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_jobs_canonical_job_id ON jobs (canonical_job_id)")

    if "inbox_jobs" not in tables:
        op.create_table(
            "inbox_jobs",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("status", sa.String(30), nullable=False, server_default="new"),
            sa.Column("captured_via", sa.String(30), nullable=False, server_default="manual"),
            sa.Column("ai_recommended_category", sa.String(50)),
            sa.Column("user_selected_category", sa.String(50)),
            sa.Column("tracker_summary", sa.String(100)),
            sa.Column("application_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("user_applications.id", ondelete="SET NULL"), unique=True),
            sa.Column("duplicate_of_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("inbox_jobs.id", ondelete="SET NULL")),
            sa.Column("notes", sa.Text()),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.CheckConstraint(
                "status IN ('new', 'ai_reviewed', 'shortlisted', 'resume_ready', 'applied', 'archived', 'duplicate')",
                name="ck_inbox_jobs_status",
            ),
            sa.UniqueConstraint("user_id", "job_id", name="uq_inbox_jobs_user_job"),
        )
        op.create_index("ix_inbox_jobs_user_id", "inbox_jobs", ["user_id"])
        op.create_index("ix_inbox_jobs_job_id", "inbox_jobs", ["job_id"])
        op.create_index("ix_inbox_jobs_status", "inbox_jobs", ["status"])

    if "user_scoring_prefs" not in tables:
        op.create_table(
            "user_scoring_prefs",
            sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
            sa.Column("work_authorization", sa.String(50), nullable=False, server_default="work_permit"),
            sa.Column("target_provinces", postgresql.ARRAY(sa.String(2)), nullable=False, server_default="{AB,BC,ON,SK}"),
            sa.Column("relocation_open", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("threshold_overrides", postgresql.JSONB()),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )


def downgrade() -> None:
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())
    if "user_scoring_prefs" in tables:
        op.drop_table("user_scoring_prefs")
    if "inbox_jobs" in tables:
        op.drop_table("inbox_jobs")
    if "jobs" in tables:
        op.execute("DROP INDEX IF EXISTS ix_jobs_canonical_url")
        op.execute("DROP INDEX IF EXISTS ix_jobs_canonical_job_id")
        op.execute("DROP INDEX IF EXISTS ix_jobs_province")
        existing_columns = {column["name"] for column in sa.inspect(bind).get_columns("jobs")}
        for column in reversed(JOB_COLUMNS):
            if column.name in existing_columns:
                op.drop_column("jobs", column.name)
