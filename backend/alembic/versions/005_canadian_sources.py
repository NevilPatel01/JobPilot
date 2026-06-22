"""Canadian source configuration and scraper run audits.

Revision ID: 005_canadian_sources
Revises: 004_resume_from_inbox
Create Date: 2026-06-21
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "005_canadian_sources"
down_revision: Union[str, None] = "004_resume_from_inbox"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())
    if "jobs" not in tables:
        return
    if "job_sources" not in tables:
        op.create_table(
            "job_sources",
            sa.Column("name", sa.String(50), primary_key=True),
            sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("rate_limit", sa.String(100)),
            sa.Column("settings_json", postgresql.JSONB(), nullable=False, server_default="{}"),
            sa.Column("last_success", sa.DateTime(timezone=True)),
            sa.Column("last_error", sa.Text()),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
    if "scraper_runs" not in tables:
        op.create_table(
            "scraper_runs",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("source", sa.String(50), nullable=False),
            sa.Column("query", sa.String(255)),
            sa.Column("city", sa.String(120)),
            sa.Column("status", sa.String(30), nullable=False),
            sa.Column("fetched_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("new_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("duplicate_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("errors", postgresql.JSONB(), nullable=False, server_default="[]"),
            sa.Column("duration_ms", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("dry_run", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("completed_at", sa.DateTime(timezone=True)),
        )
        op.create_index("ix_scraper_runs_source", "scraper_runs", ["source"])
        op.create_index("ix_scraper_runs_status", "scraper_runs", ["status"])


def downgrade() -> None:
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())
    if "scraper_runs" in tables:
        op.drop_table("scraper_runs")
    if "job_sources" in tables:
        op.drop_table("job_sources")
