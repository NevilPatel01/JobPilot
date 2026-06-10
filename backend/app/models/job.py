import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    salary_min: Mapped[int | None] = mapped_column(Integer)
    salary_max: Mapped[int | None] = mapped_column(Integer)
    salary_currency: Mapped[str] = mapped_column(String(8), default="USD")
    location: Mapped[str | None] = mapped_column(String(255))
    country: Mapped[str | None] = mapped_column(String(2), index=True)
    is_remote: Mapped[bool] = mapped_column(Boolean, default=True)
    tech_stack: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    employment_type: Mapped[str | None] = mapped_column(String(50))
    source: Mapped[str] = mapped_column(String(100), default="custom")
    source_id: Mapped[str | None] = mapped_column(String(255))
    dedup_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_verified: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    expired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    search_vector = mapped_column(TSVECTOR, nullable=True)
