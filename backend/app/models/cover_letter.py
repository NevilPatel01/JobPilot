import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CoverLetterDocument(Base):
    __tablename__ = "cover_letter_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    resume_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resume_documents.id", ondelete="SET NULL")
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    hiring_manager_name: Mapped[str | None] = mapped_column(String(255))
    hiring_manager_email: Mapped[str | None] = mapped_column(String(255))
    street_address: Mapped[str | None] = mapped_column(String(500))
    city: Mapped[str | None] = mapped_column(String(100))
    state_province: Mapped[str | None] = mapped_column(String(100))
    postal_code: Mapped[str | None] = mapped_column(String(20))
    letter_date: Mapped[str | None] = mapped_column(String(50))
    additional_context: Mapped[str | None] = mapped_column(Text)
    content_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    latex_source: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user = relationship("User", back_populates="cover_letters")
    resume = relationship("ResumeDocument", back_populates="cover_letter", foreign_keys=[resume_id])
    chat_messages = relationship(
        "CoverLetterChatMessage", back_populates="cover_letter", cascade="all, delete-orphan"
    )


class CoverLetterChatMessage(Base):
    __tablename__ = "cover_letter_chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cover_letter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cover_letter_documents.id", ondelete="CASCADE")
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    cover_letter = relationship("CoverLetterDocument", back_populates="chat_messages")
    pending_changes = relationship(
        "CoverLetterPendingChange", back_populates="message", cascade="all, delete-orphan"
    )


class CoverLetterPendingChange(Base):
    __tablename__ = "cover_letter_pending_changes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cover_letter_chat_messages.id", ondelete="CASCADE")
    )
    path: Mapped[str] = mapped_column(String(500), nullable=False)
    old_value: Mapped[str | None] = mapped_column(Text)
    new_value: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    message = relationship("CoverLetterChatMessage", back_populates="pending_changes")
