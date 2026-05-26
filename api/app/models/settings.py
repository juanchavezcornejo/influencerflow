"""AppSetting model — key-value store for runtime configuration."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base

SETTING_KEYS: frozenset[str] = frozenset(
    {
        "claude_api_key",
        "replicate_api_key",
        "google_client_id",
        "google_client_secret",
        "session_budget_usd",
        "session_hard_cap_usd",
        "style_seed",
    }
)

SENSITIVE_KEYS: frozenset[str] = frozenset(
    {
        "claude_api_key",
        "replicate_api_key",
        "google_client_secret",
    }
)


class AppSetting(Base):
    """Runtime-configurable settings stored encrypted in DB."""

    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        server_default=func.now(),
    )
