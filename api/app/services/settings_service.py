"""Settings service — read/write app_settings with Fernet encryption and response masking."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings as app_config
from app.models.settings import SENSITIVE_KEYS
from app.repositories.settings import SettingsRepository
from app.schemas.settings import SettingsPatch, SettingsResponse

logger = logging.getLogger(__name__)


@dataclass
class EffectiveSettings:
    """Plaintext (unmasked) settings for internal use only. Never expose to API responses."""

    claude_api_key: str | None
    replicate_api_key: str | None
    google_client_id: str | None
    google_client_secret: str | None
    session_budget_usd: float
    session_hard_cap_usd: float
    style_seed: str | None


# Mapping from SettingsPatch field name (camelCase) to DB key (snake_case)
_FIELD_TO_KEY: dict[str, str] = {
    "claudeApiKey": "claude_api_key",
    "replicateApiKey": "replicate_api_key",
    "googleClientId": "google_client_id",
    "googleClientSecret": "google_client_secret",
    "sessionBudgetUsd": "session_budget_usd",
    "sessionHardCapUsd": "session_hard_cap_usd",
    "styleSeed": "style_seed",
}


def _encrypt(value: str) -> str:
    f = Fernet(app_config.fernet_key.encode())
    return f.encrypt(value.encode()).decode()


def _decrypt(value: str) -> str | None:
    try:
        f = Fernet(app_config.fernet_key.encode())
        return f.decrypt(value.encode()).decode()
    except (InvalidToken, Exception):
        logger.warning("Failed to decrypt settings value")
        return None


def _mask(value: str | None) -> str | None:
    """Return ****last4 or None if value is too short/absent."""
    if not value or len(value) <= 4:
        return None
    return f"****{value[-4:]}"


class SettingsService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = SettingsRepository(db)

    async def get_effective(self) -> EffectiveSettings:
        """Return all settings with plaintext (unmasked) values for internal use."""
        raw = await self.repo.get_all()

        def _read_plain(key: str, env_default: str | None = None) -> str | None:
            val = raw.get(key)
            if val is None:
                return env_default
            return val

        def _read_sensitive(key: str, env_default: str | None = None) -> str | None:
            val = raw.get(key)
            if val is None:
                return env_default
            return _decrypt(val)

        claude_key = _read_sensitive("claude_api_key") or (app_config.anthropic_api_key or None)
        replicate_key = _read_sensitive("replicate_api_key") or (
            app_config.replicate_api_token or None
        )
        google_secret = _read_sensitive("google_client_secret") or (
            app_config.google_oauth_client_secret or None
        )

        budget_str = _read_plain("session_budget_usd")
        hard_cap_str = _read_plain("session_hard_cap_usd")

        return EffectiveSettings(
            claude_api_key=claude_key,
            replicate_api_key=replicate_key,
            google_client_id=_read_plain("google_client_id")
            or (app_config.google_oauth_client_id or None),
            google_client_secret=google_secret,
            session_budget_usd=float(budget_str) if budget_str else app_config.session_budget_usd,
            session_hard_cap_usd=float(hard_cap_str)
            if hard_cap_str
            else app_config.session_hard_cap_usd,
            style_seed=_read_plain("style_seed"),
        )

    async def get(self) -> SettingsResponse:
        """Return all settings. Sensitive values are decrypted then masked for the response."""
        raw = await self.repo.get_all()

        def _read_plain(key: str, env_default: str | None = None) -> str | None:
            val = raw.get(key)
            if val is None:
                return env_default
            return val

        def _read_sensitive(key: str, env_default: str | None = None) -> str | None:
            val = raw.get(key)
            if val is None:
                return env_default
            return _decrypt(val)

        claude_key = _read_sensitive("claude_api_key") or (app_config.anthropic_api_key or None)
        replicate_key = _read_sensitive("replicate_api_key") or (
            app_config.replicate_api_token or None
        )
        google_secret = _read_sensitive("google_client_secret") or (
            app_config.google_oauth_client_secret or None
        )

        budget_str = _read_plain("session_budget_usd")
        hard_cap_str = _read_plain("session_hard_cap_usd")

        return SettingsResponse(
            claudeApiKey=_mask(claude_key),
            replicateApiKey=_mask(replicate_key),
            googleClientId=_read_plain("google_client_id")
            or (app_config.google_oauth_client_id or None),
            googleClientSecret=_mask(google_secret),
            sessionBudgetUsd=float(budget_str) if budget_str else app_config.session_budget_usd,
            sessionHardCapUsd=float(hard_cap_str)
            if hard_cap_str
            else app_config.session_hard_cap_usd,
            styleSeed=_read_plain("style_seed"),
        )

    async def patch(self, patch: SettingsPatch) -> SettingsResponse:
        """Apply partial update. Sensitive keys are encrypted before storage."""
        for field, key in _FIELD_TO_KEY.items():
            value = getattr(patch, field)
            if value is None:
                continue  # omitted — leave unchanged
            if isinstance(value, float):
                str_value: str = str(value)
            else:
                str_value = str(value)
            if key in SENSITIVE_KEYS and str_value:
                str_value = _encrypt(str_value)
            await self.repo.set(key, str_value)
        return await self.get()
