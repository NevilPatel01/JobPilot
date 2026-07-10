"""Audit logs, AgentRun AI-provenance columns, UserApplication status constraint.

Revision ID: 007_audit_and_provenance
Revises: 006_extension_capture
Create Date: 2026-07-10
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "007_audit_and_provenance"
down_revision: Union[str, None] = "006_extension_capture"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())

    if "users" in tables and "audit_logs" not in tables:
        op.create_table(
            "audit_logs",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")),
            sa.Column("action", sa.String(120), nullable=False),
            sa.Column("entity_type", sa.String(60), nullable=False),
            sa.Column("entity_id", sa.String(64), nullable=False),
            sa.Column("before_json", postgresql.JSONB()),
            sa.Column("after_json", postgresql.JSONB()),
            sa.Column("model_name", sa.String(100)),
            sa.Column("prompt_version", sa.String(50)),
            sa.Column("confidence", sa.Float()),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
        op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
        op.create_index("ix_audit_logs_entity_type", "audit_logs", ["entity_type"])
        op.create_index("ix_audit_logs_entity_id", "audit_logs", ["entity_id"])

    if "agent_runs" in tables:
        cols = {c["name"] for c in sa.inspect(bind).get_columns("agent_runs")}
        if "model_name" not in cols:
            op.add_column("agent_runs", sa.Column("model_name", sa.String(100)))
        if "prompt_version" not in cols:
            op.add_column("agent_runs", sa.Column("prompt_version", sa.String(50)))
        if "confidence" not in cols:
            op.add_column("agent_runs", sa.Column("confidence", sa.Float()))

    if "user_applications" in tables:
        constraints = {c["name"] for c in sa.inspect(bind).get_check_constraints("user_applications")}
        if "ck_user_applications_status" not in constraints:
            op.create_check_constraint(
                "ck_user_applications_status",
                "user_applications",
                "status IN ('to_apply', 'applied', 'interviewing', 'offer', 'rejected')",
            )


def downgrade() -> None:
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())

    if "user_applications" in tables:
        constraints = {c["name"] for c in sa.inspect(bind).get_check_constraints("user_applications")}
        if "ck_user_applications_status" in constraints:
            op.drop_constraint("ck_user_applications_status", "user_applications", type_="check")

    if "agent_runs" in tables:
        cols = {c["name"] for c in sa.inspect(bind).get_columns("agent_runs")}
        for col in ("confidence", "prompt_version", "model_name"):
            if col in cols:
                op.drop_column("agent_runs", col)

    if "audit_logs" in tables:
        op.drop_table("audit_logs")
