"""Description model — AI-generated captions for groups."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Description(Base):
    """AI-generated description/caption for a group."""

    __tablename__ = "descriptions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: __import__("uuid").uuid4().hex
    )
    group_id: Mapped[str] = mapped_column(String(36), ForeignKey("groups.id"), index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    custom_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_used: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tokens_in: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_out: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True
    )
