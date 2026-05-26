"""Session model — tracks a sync from a cloud folder."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Session(Base):
    """Represents a resync session from a cloud folder."""

    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: __import__("uuid").uuid4().hex
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    cloud_provider: Mapped[str] = mapped_column(String(50))  # "google_drive"
    cloud_folder_id: Mapped[str] = mapped_column(String(255))
    cloud_folder_name: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(
        String(50), default="pending", index=True
    )  # pending, syncing, ready, error, deleted
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
