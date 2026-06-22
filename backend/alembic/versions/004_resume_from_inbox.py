"""Resume category templates and Inbox resume linkage.

Revision ID: 004_resume_from_inbox
Revises: 003_fit_scoring
Create Date: 2026-06-21
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "004_resume_from_inbox"
down_revision: Union[str, None] = "003_fit_scoring"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if not {"users", "jobs", "inbox_jobs", "resume_documents"}.issubset(tables):
        return

    if "resume_category_templates" not in tables:
        op.create_table(
            "resume_category_templates",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("category", sa.String(50), nullable=False),
            sa.Column("base_content", postgresql.JSONB(), nullable=False),
            sa.Column("selection_notes", postgresql.JSONB(), nullable=False),
            sa.Column("generated_from_profile_at", sa.DateTime(timezone=True)),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.UniqueConstraint("user_id", "category", name="uq_resume_category_templates_user_category"),
        )
        op.create_index("ix_resume_category_templates_user_id", "resume_category_templates", ["user_id"])

    resume_columns = {column["name"] for column in inspector.get_columns("resume_documents")}
    resume_additions = (
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id", ondelete="SET NULL")),
        sa.Column("inbox_job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("inbox_jobs.id", ondelete="SET NULL")),
        sa.Column("resume_category", sa.String(50)),
        sa.Column("why_this_version", postgresql.JSONB()),
    )
    for column in resume_additions:
        if column.name not in resume_columns:
            op.add_column("resume_documents", column)
    op.execute("CREATE INDEX IF NOT EXISTS ix_resume_documents_job_id ON resume_documents (job_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_resume_documents_inbox_job_id ON resume_documents (inbox_job_id)")

    inbox_columns = {column["name"] for column in sa.inspect(bind).get_columns("inbox_jobs")}
    if "resume_id" not in inbox_columns:
        op.add_column(
            "inbox_jobs",
            sa.Column(
                "resume_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("resume_documents.id", ondelete="SET NULL"),
            ),
        )
        op.create_unique_constraint("uq_inbox_jobs_resume_id", "inbox_jobs", ["resume_id"])


def downgrade() -> None:
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())
    if "inbox_jobs" in tables:
        columns = {column["name"] for column in sa.inspect(bind).get_columns("inbox_jobs")}
        if "resume_id" in columns:
            op.drop_constraint("uq_inbox_jobs_resume_id", "inbox_jobs", type_="unique")
            op.drop_column("inbox_jobs", "resume_id")
    if "resume_documents" in tables:
        op.execute("DROP INDEX IF EXISTS ix_resume_documents_inbox_job_id")
        op.execute("DROP INDEX IF EXISTS ix_resume_documents_job_id")
        columns = {column["name"] for column in sa.inspect(bind).get_columns("resume_documents")}
        for name in ("why_this_version", "resume_category", "inbox_job_id", "job_id"):
            if name in columns:
                op.drop_column("resume_documents", name)
    if "resume_category_templates" in tables:
        op.drop_table("resume_category_templates")
