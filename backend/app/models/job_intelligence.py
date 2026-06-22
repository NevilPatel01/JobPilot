import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


INBOX_STATUSES = (
    "new",
    "ai_reviewed",
    "shortlisted",
    "resume_ready",
    "applied",
    "archived",
    "duplicate",
)


class InboxJob(Base):
    __tablename__ = "inbox_jobs"
    __table_args__ = (
        UniqueConstraint("user_id", "job_id", name="uq_inbox_jobs_user_job"),
        CheckConstraint(
            "status IN ('new', 'ai_reviewed', 'shortlisted', 'resume_ready', 'applied', 'archived', 'duplicate')",
            name="ck_inbox_jobs_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="new", index=True)
    captured_via: Mapped[str] = mapped_column(String(30), nullable=False, default="manual")
    ai_recommended_category: Mapped[str | None] = mapped_column(String(50))
    user_selected_category: Mapped[str | None] = mapped_column(String(50))
    tracker_summary: Mapped[str | None] = mapped_column(String(100))
    application_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user_applications.id", ondelete="SET NULL"), unique=True
    )
    fit_score_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job_fit_scores.id", ondelete="SET NULL"), unique=True
    )
    resume_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resume_documents.id", ondelete="SET NULL"), unique=True
    )
    duplicate_of_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inbox_jobs.id", ondelete="SET NULL")
    )
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    job = relationship("Job", back_populates="inbox_entries")
    application = relationship("UserApplication")
    fit_score = relationship("JobFitScore", foreign_keys=[fit_score_id], post_update=True)
    resume = relationship("ResumeDocument", foreign_keys=[resume_id], post_update=True)


class JobFitScore(Base):
    __tablename__ = "job_fit_scores"
    __table_args__ = (UniqueConstraint("user_id", "job_id", name="uq_job_fit_scores_user_job"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    score: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    signals: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    matched_skills: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    missing_skills: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    risk_flags: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    recommended_action: Mapped[str] = mapped_column(String(120), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_category: Mapped[str | None] = mapped_column(String(50))
    category_confidence: Mapped[int | None] = mapped_column(Integer)
    scored_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class UserScoringPrefs(Base):
    __tablename__ = "user_scoring_prefs"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    work_authorization: Mapped[str] = mapped_column(String(50), nullable=False, default="work_permit")
    target_provinces: Mapped[list[str]] = mapped_column(
        ARRAY(String(2)), nullable=False, default=lambda: ["AB", "BC", "ON", "SK"]
    )
    relocation_open: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    threshold_overrides: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ResumeCategoryTemplate(Base):
    __tablename__ = "resume_category_templates"
    __table_args__ = (UniqueConstraint("user_id", "category", name="uq_resume_category_templates_user_category"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    base_content: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    selection_notes: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    generated_from_profile_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class JobSourceConfig(Base):
    __tablename__ = "job_sources"

    name: Mapped[str] = mapped_column(String(50), primary_key=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    rate_limit: Mapped[str | None] = mapped_column(String(100))
    settings_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    last_success: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ScraperRun(Base):
    __tablename__ = "scraper_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    query: Mapped[str | None] = mapped_column(String(255))
    city: Mapped[str | None] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    fetched_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    new_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duplicate_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    errors: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    dry_run: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CapturedJob(Base):
    __tablename__ = "captured_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="SET NULL"), index=True
    )
    inbox_job_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inbox_jobs.id", ondelete="SET NULL"), index=True
    )
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    source_site: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="received", index=True)
    action: Mapped[str] = mapped_column(String(20), nullable=False, default="inbox")
    raw_payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
