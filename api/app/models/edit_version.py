"""Edit version model — tracks edits and versions of assets."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class EditVersion(Base):
    """A version of an asset with applied corrections."""

    __tablename__ = "edit_versions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: __import__("uuid").uuid4().hex
    )
    asset_id: Mapped[str] = mapped_column(String(36), ForeignKey("assets.id"), index=True)
    parent_version_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("edit_versions.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True
    )
    changes_log_text: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # Human-readable bullet points
    corrections_applied_json: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # JSON dict of corrections
    output_path: Mapped[str | None] = mapped_column(
        String(1024), nullable=True
    )  # Path to full-res output
    user_decision: Mapped[str | None] = mapped_column(
        String(50), nullable=True, index=True
    )  # accepted, rejected
