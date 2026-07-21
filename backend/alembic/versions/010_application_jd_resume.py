"""Add job_description, resume_id, uploaded resume fields to user_applications.

Revision ID: 010_application_jd_resume
Revises: 009_github_projects
Create Date: 2026-07-20
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "010_application_jd_resume"
down_revision: Union[str, None] = "009_github_projects"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    tables = sa.inspect(bind).get_table_names()
    if "user_applications" not in tables:
        return
    columns = {c["name"] for c in sa.inspect(bind).get_columns("user_applications")}
    if "job_description" not in columns:
        op.add_column("user_applications", sa.Column("job_description", sa.Text(), nullable=True))
    if "resume_id" not in columns:
        op.add_column(
            "user_applications",
            sa.Column(
                "resume_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("resume_documents.id", ondelete="SET NULL"),
                nullable=True,
            ),
        )
    if "uploaded_resume_filename" not in columns:
        op.add_column(
            "user_applications",
            sa.Column("uploaded_resume_filename", sa.String(length=255), nullable=True),
        )


def downgrade() -> None:
    bind = op.get_bind()
    tables = sa.inspect(bind).get_table_names()
    if "user_applications" not in tables:
        return
    columns = {c["name"] for c in sa.inspect(bind).get_columns("user_applications")}
    if "uploaded_resume_filename" in columns:
        op.drop_column("user_applications", "uploaded_resume_filename")
    if "resume_id" in columns:
        op.drop_column("user_applications", "resume_id")
    if "job_description" in columns:
        op.drop_column("user_applications", "job_description")
