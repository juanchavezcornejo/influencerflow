"""Cost log model — tracks API usage and costs."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class CostLog(Base):
    """Log of API usage and estimated costs."""

    __tablename__ = "cost_log"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: __import__("uuid").uuid4().hex
    )
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("sessions.id"), index=True)
    operation: Mapped[str] = mapped_column(
        String(100), index=True
    )  # "grouping_ai", "color_ai", "object_removal", etc
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tokens_in: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_out: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dollars_estimate: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True
    )
