"""Pydantic schemas for /settings endpoints."""

from __future__ import annotations

from pydantic import BaseModel


class SettingsResponse(BaseModel):
    """GET /settings response. Sensitive keys are masked (****last4)."""

    claudeApiKey: str | None
    replicateApiKey: str | None
    googleClientId: str | None
    googleClientSecret: str | None
    sessionBudgetUsd: float
    sessionHardCapUsd: float
    styleSeed: str | None


class SettingsPatch(BaseModel):
    """PATCH /settings body. Omitted fields leave current value unchanged. Explicit null clears."""

    claudeApiKey: str | None = None
    replicateApiKey: str | None = None
    googleClientId: str | None = None
    googleClientSecret: str | None = None
    sessionBudgetUsd: float | None = None
    sessionHardCapUsd: float | None = None
    styleSeed: str | None = None
