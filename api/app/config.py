"""Application settings (loaded from environment / .env)."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


@dataclass
class RuntimeSettings:
    """Merged settings from DB + env, with plaintext secrets. For internal use only."""

    anthropic_api_key: str
    replicate_api_token: str
    google_oauth_client_id: str
    google_oauth_client_secret: str
    google_oauth_redirect_uri: str
    session_budget_usd: float
    session_hard_cap_usd: float
    style_seed_text: str


class Settings(BaseSettings):
    """Environment-backed configuration.

    Values are read from (in order): actual environment, ``.env`` file,
    defaults defined below.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Environment flag
    environment: str = "development"

    # Infra
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/influencerflow"
    redis_url: str = "redis://localhost:6379/0"
    data_dir: Path = Path("/data")

    # Security (populated in later weeks)
    jwt_secret: str = "dev-insecure-change-me"
    fernet_key: str = ""

    # Single-user seed
    single_user_email: str = ""
    single_user_password: str = ""

    # External integrations (populated later)
    google_oauth_client_id: str = ""
    google_oauth_client_secret: str = ""
    google_oauth_redirect_uri: str = "http://localhost:8000/api/v1/storage/google/oauth/callback"
    anthropic_api_key: str = ""
    replicate_api_token: str = ""

    # Budget guards
    session_budget_usd: float = 10.0
    session_hard_cap_usd: float = 50.0

    @property
    def is_development(self) -> bool:
        return self.environment.lower() in {"development", "dev", "local"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached accessor. Reload with ``get_settings.cache_clear()`` in tests."""
    return Settings()


settings = get_settings()
