"""Storage provider credentials (encrypted at rest)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class StorageCredentials(Base):
    """OAuth tokens for cloud storage providers. Stored encrypted."""

    __tablename__ = "storage_credentials"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: __import__("uuid").uuid4().hex
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    provider: Mapped[str] = mapped_column(String(50), index=True)  # "google_drive", etc.
    refresh_token: Mapped[str] = mapped_column(Text)  # Encrypted via Fernet
    access_token: Mapped[str | None] = mapped_column(Text, nullable=True)  # Encrypted
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    __table_args__ = (UniqueConstraint("user_id", "provider", name="uq_storage_user_provider"),)
