"""Asset model — represents a photo or video file."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Asset(Base):
    """A photo or video downloaded from cloud storage."""

    __tablename__ = "assets"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: __import__("uuid").uuid4().hex
    )
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("sessions.id"), index=True)
    original_cloud_path: Mapped[str] = mapped_column(String(1024))
    original_filename: Mapped[str] = mapped_column(String(255))
    preview_path: Mapped[str | None] = mapped_column(
        String(1024), nullable=True
    )  # /data/previews/...
    thumbnail_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    full_res_local_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    exif_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON-serialized EXIF
    gps_lat: Mapped[float | None] = mapped_column(Float, nullable=True, index=True)
    gps_lng: Mapped[float | None] = mapped_column(Float, nullable=True, index=True)
    taken_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    is_video: Mapped[bool] = mapped_column(Boolean, default=False)
    has_face: Mapped[bool] = mapped_column(Boolean, default=False)
    aesthetic_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    phash: Mapped[str | None] = mapped_column(String(16), nullable=True, index=True)  # hex string
    status: Mapped[str] = mapped_column(String(50), default="active")  # active, rejected
    near_duplicate_cluster_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    __table_args__ = (
        Index("ix_asset_session_taken", "session_id", "taken_at"),
        Index("ix_asset_session_phash", "session_id", "phash"),
    )
