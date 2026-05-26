"""AI cache model — stores cached API responses."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class AICache(Base):
    """Cached response from AI APIs (Claude, Replicate, etc)."""

    __tablename__ = "ai_cache"

    cache_key: Mapped[str] = mapped_column(String(64), primary_key=True)
    response_json: Mapped[str] = mapped_column(Text)
    model_used: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tokens_in: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_out: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True
    )
