"""Raw extension capture audit records.

Revision ID: 006_extension_capture
Revises: 005_canadian_sources
Create Date: 2026-06-22
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "006_extension_capture"
down_revision: Union[str, None] = "005_canadian_sources"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())
    if not {"users", "jobs", "inbox_jobs"}.issubset(tables) or "captured_jobs" in tables:
        return
    op.create_table(
        "captured_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id", ondelete="SET NULL")),
        sa.Column("inbox_job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("inbox_jobs.id", ondelete="SET NULL")),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("source_site", sa.String(50)),
        sa.Column("status", sa.String(30), nullable=False, server_default="received"),
        sa.Column("action", sa.String(20), nullable=False, server_default="inbox"),
        sa.Column("raw_payload", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("error", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_captured_jobs_user_id", "captured_jobs", ["user_id"])
    op.create_index("ix_captured_jobs_job_id", "captured_jobs", ["job_id"])
    op.create_index("ix_captured_jobs_inbox_job_id", "captured_jobs", ["inbox_job_id"])
    op.create_index("ix_captured_jobs_status", "captured_jobs", ["status"])


def downgrade() -> None:
    if "captured_jobs" in set(sa.inspect(op.get_bind()).get_table_names()):
        op.drop_table("captured_jobs")
