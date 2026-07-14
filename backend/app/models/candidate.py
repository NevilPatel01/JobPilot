import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

FACT_TYPES = (
    "personal", "contact", "work_authorization", "location", "target_role",
    "target_industry", "employment", "education", "certification",
    "project", "skill", "achievement", "metric",
)
FACT_SOURCES = ("user_entered", "resume_upload", "linkedin_import", "inferred", "github_import")
VERIFICATION_STATUSES = ("unverified", "user_confirmed", "contradicted")
ANSWER_CATEGORIES = (
    "behavioral", "logistics", "salary", "work_authorization",
    "demographic", "legal_declaration", "other",
)
SENSITIVE_ANSWER_CATEGORIES = {"salary", "work_authorization", "demographic", "legal_declaration"}


def _in_clause(values: tuple[str, ...]) -> str:
    return "(" + ", ".join(f"'{v}'" for v in values) + ")"


class CandidateFact(Base):
    __tablename__ = "candidate_facts"
    __table_args__ = (
        CheckConstraint(f"fact_type IN {_in_clause(FACT_TYPES)}", name="ck_candidate_facts_fact_type"),
        CheckConstraint(f"source IN {_in_clause(FACT_SOURCES)}", name="ck_candidate_facts_source"),
        CheckConstraint(
            f"verification_status IN {_in_clause(VERIFICATION_STATUSES)}",
            name="ck_candidate_facts_verification_status",
        ),
        Index("ix_candidate_facts_user_type", "user_id", "fact_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    fact_type: Mapped[str] = mapped_column(String(30), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    source: Mapped[str] = mapped_column(String(30), nullable=False, default="user_entered")
    verification_status: Mapped[str] = mapped_column(String(20), nullable=False, default="unverified")
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    superseded_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidate_facts.id", ondelete="SET NULL")
    )
    is_prohibited: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class CandidateDigest(Base):
    """Derived, regenerable prompt artifact (e.g. the GitHub projects brief).
    Never a source of truth — always rebuildable from candidate_facts."""

    __tablename__ = "candidate_digests"
    __table_args__ = (UniqueConstraint("user_id", "kind", name="uq_candidate_digests_user_kind"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    kind: Mapped[str] = mapped_column(String(30), nullable=False)
    content_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    source_fact_ids: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(UUID(as_uuid=True)), nullable=False, default=list
    )
    sync_state_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    token_estimate: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Achievement(Base):
    __tablename__ = "achievements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    related_fact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidate_facts.id", ondelete="SET NULL")
    )
    situation: Mapped[str] = mapped_column(Text, nullable=False, default="")
    task: Mapped[str] = mapped_column(Text, nullable=False, default="")
    action: Mapped[str] = mapped_column(Text, nullable=False, default="")
    result: Mapped[str] = mapped_column(Text, nullable=False, default="")
    metrics: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    tags: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    verification_status: Mapped[str] = mapped_column(String(20), nullable=False, default="unverified")
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    source: Mapped[str] = mapped_column(String(30), nullable=False, default="user_entered")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class CareerProfile(Base):
    __tablename__ = "career_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    emphasis_fact_ids: Mapped[list[uuid.UUID]] = mapped_column(ARRAY(UUID(as_uuid=True)), nullable=False, default=list)
    positioning_statement: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class AnswerBankEntry(Base):
    __tablename__ = "answer_bank_entries"
    __table_args__ = (
        CheckConstraint(f"question_category IN {_in_clause(ANSWER_CATEGORIES)}", name="ck_answer_bank_category"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_category: Mapped[str] = mapped_column(String(30), nullable=False)
    answer_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_sensitive: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    related_fact_ids: Mapped[list[uuid.UUID]] = mapped_column(ARRAY(UUID(as_uuid=True)), nullable=False, default=list)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    usage_count: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
