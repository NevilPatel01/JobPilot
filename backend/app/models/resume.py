import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ResumeDocument(Base):
    __tablename__ = "resume_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    job_description: Mapped[str | None] = mapped_column(Text)
    company_url: Mapped[str | None] = mapped_column(String(500))
    company_name: Mapped[str | None] = mapped_column(String(255))
    source_type: Mapped[str] = mapped_column(String(20), default="profile")
    content_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    latex_source: Mapped[str | None] = mapped_column(Text)
    insights_json: Mapped[dict | None] = mapped_column(JSONB)
    application_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user_applications.id", ondelete="SET NULL")
    )
    job_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="SET NULL"), index=True
    )
    inbox_job_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inbox_jobs.id", ondelete="SET NULL"), index=True
    )
    resume_category: Mapped[str | None] = mapped_column(String(50))
    why_this_version: Mapped[dict | None] = mapped_column(JSONB)
    create_cover_letter: Mapped[bool] = mapped_column(Boolean, default=False)
    cover_letter_meta: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user = relationship("User", back_populates="resumes")
    cover_letter = relationship("CoverLetterDocument", back_populates="resume", foreign_keys="CoverLetterDocument.resume_id")
    agent_runs = relationship("AgentRun", back_populates="resume", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="resume", cascade="all, delete-orphan")
    ats_scores = relationship("ATSScore", back_populates="resume", cascade="all, delete-orphan")


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resume_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resume_documents.id", ondelete="CASCADE")
    )
    agent_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    steps_json: Mapped[dict | None] = mapped_column(JSONB)
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    resume = relationship("ResumeDocument", back_populates="agent_runs")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resume_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resume_documents.id", ondelete="CASCADE")
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    pending_diffs_json: Mapped[list | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    resume = relationship("ResumeDocument", back_populates="chat_messages")
    pending_changes = relationship("PendingChange", back_populates="message", cascade="all, delete-orphan")


class PendingChange(Base):
    __tablename__ = "pending_changes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chat_messages.id", ondelete="CASCADE")
    )
    path: Mapped[str] = mapped_column(String(500), nullable=False)
    old_value: Mapped[str | None] = mapped_column(Text)
    new_value: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    message = relationship("ChatMessage", back_populates="pending_changes")


class ATSScore(Base):
    __tablename__ = "ats_scores"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resume_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resume_documents.id", ondelete="CASCADE")
    )
    job_description: Mapped[str | None] = mapped_column(Text)
    overall_score: Mapped[int] = mapped_column(default=0)
    keyword_match: Mapped[int] = mapped_column(default=0)
    formatting_score: Mapped[int] = mapped_column(default=0)
    semantic_score: Mapped[int] = mapped_column(default=0)
    skills_coverage: Mapped[int] = mapped_column(default=0)
    section_score: Mapped[int] = mapped_column(default=0)
    matched_keywords: Mapped[list | None] = mapped_column(JSONB)
    suggestions_json: Mapped[dict | None] = mapped_column(JSONB)
    breakdown_json: Mapped[dict | None] = mapped_column(JSONB)
    missing_keywords: Mapped[list | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    resume = relationship("ResumeDocument", back_populates="ats_scores")
