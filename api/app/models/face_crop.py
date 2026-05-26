"""Face crop model — stores face crops for retouch workflow."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class FaceCrop(Base):
    """A cropped face from an asset for retouch."""

    __tablename__ = "face_crops"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: __import__("uuid").uuid4().hex
    )
    asset_id: Mapped[str] = mapped_column(String(36), ForeignKey("assets.id"), index=True)
    bbox_json: Mapped[str] = mapped_column(Text)  # {top, right, bottom, left}
    landmarks_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # 68 facial landmarks
    crop_path: Mapped[str] = mapped_column(String(1024))  # Path to original crop PNG
    user_uploaded_path: Mapped[str | None] = mapped_column(
        String(1024), nullable=True
    )  # Path to user-edited crop
    blended_output_path: Mapped[str | None] = mapped_column(
        String(1024), nullable=True
    )  # Path to final blended result
    status: Mapped[str] = mapped_column(
        String(50), default="cropped", index=True
    )  # cropped, uploaded, blended
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
