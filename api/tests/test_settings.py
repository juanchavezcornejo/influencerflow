"""Tests for the settings feature."""

from __future__ import annotations

import os

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool

from app.config import settings as app_config
from app.db import Base
from app.lib.jwt_utils import create_jwt_token
from app.models.settings import SENSITIVE_KEYS, SETTING_KEYS, AppSetting
from app.repositories.settings import SettingsRepository
from app.schemas.settings import SettingsPatch, SettingsResponse
from app.services.settings_service import SettingsService

_fernet_key = os.environ.get("FERNET_KEY") or Fernet.generate_key().decode()


def test_app_setting_model_has_expected_columns():
    cols = {c.name for c in AppSetting.__table__.columns}
    assert "key" in cols
    assert "value" in cols
    assert "updated_at" in cols


def test_setting_keys_includes_all_expected():
    assert "claude_api_key" in SETTING_KEYS
    assert "replicate_api_key" in SETTING_KEYS
    assert "style_seed" in SETTING_KEYS
    assert len(SETTING_KEYS) == 7


def test_sensitive_keys_subset_of_setting_keys():
    assert SENSITIVE_KEYS.issubset(SETTING_KEYS)
    assert "claude_api_key" in SENSITIVE_KEYS
    assert "style_seed" not in SENSITIVE_KEYS


def test_settings_response_shape():
    r = SettingsResponse(
        claudeApiKey="****1234",
        replicateApiKey=None,
        googleClientId="123.apps.googleusercontent.com",
        googleClientSecret=None,
        sessionBudgetUsd=10.0,
        sessionHardCapUsd=50.0,
        styleSeed="Warm tones",
    )
    assert r.claudeApiKey == "****1234"
    assert r.sessionBudgetUsd == 10.0


def test_settings_patch_all_fields_optional():
    p = SettingsPatch()  # no args — all optional
    assert p.claudeApiKey is None
    assert p.styleSeed is None


def test_settings_patch_partial():
    p = SettingsPatch(styleSeed="Moody vibes")
    assert p.styleSeed == "Moody vibes"
    assert p.claudeApiKey is None


@pytest.fixture
async def db():
    """In-memory SQLite DB (matches project test pattern)."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_get_all_returns_empty_dict_when_no_rows(db: AsyncSession):
    repo = SettingsRepository(db)
    result = await repo.get_all()
    assert result == {}


@pytest.mark.asyncio
async def test_set_and_get(db: AsyncSession):
    repo = SettingsRepository(db)
    await repo.set("style_seed", "Warm, golden tones")
    result = await repo.get_all()
    assert result["style_seed"] == "Warm, golden tones"


@pytest.mark.asyncio
async def test_set_many_updates_multiple_keys(db: AsyncSession):
    repo = SettingsRepository(db)
    await repo.set_many({"session_budget_usd": "15.0", "session_hard_cap_usd": "75.0"})
    result = await repo.get_all()
    assert result["session_budget_usd"] == "15.0"
    assert result["session_hard_cap_usd"] == "75.0"


@pytest.mark.asyncio
async def test_service_get_returns_env_budget_defaults(db):
    """When DB is empty, budget values come from app config defaults."""
    service = SettingsService(db)
    response = await service.get()
    assert response.sessionBudgetUsd == 10.0  # config.py default
    assert response.sessionHardCapUsd == 50.0


@pytest.mark.asyncio
async def test_service_sensitive_keys_are_masked(db):
    """Stored encrypted value should appear masked in response."""
    repo = SettingsRepository(db)
    f = Fernet(app_config.fernet_key.encode())
    encrypted = f.encrypt(b"sk-ant-api03-realkey9876").decode()
    await repo.set("claude_api_key", encrypted)
    await db.flush()

    service = SettingsService(db)
    response = await service.get()
    assert response.claudeApiKey == "****9876"
    assert "realkey" not in (response.claudeApiKey or "")


@pytest.mark.asyncio
async def test_service_patch_encrypts_sensitive_key(db):
    """Patching a sensitive key should store it encrypted, not plaintext."""
    service = SettingsService(db)
    await service.patch(SettingsPatch(claudeApiKey="sk-ant-api03-mynewkey5678"))
    await db.flush()

    repo = SettingsRepository(db)
    all_settings = await repo.get_all()
    stored = all_settings.get("claude_api_key")

    assert stored is not None
    assert stored != "sk-ant-api03-mynewkey5678"  # must not be plaintext

    f = Fernet(app_config.fernet_key.encode())
    decrypted = f.decrypt(stored.encode()).decode()
    assert decrypted == "sk-ant-api03-mynewkey5678"


@pytest.mark.asyncio
async def test_service_patch_non_sensitive_key_not_encrypted(db):
    """style_seed should be stored as plaintext."""
    service = SettingsService(db)
    await service.patch(SettingsPatch(styleSeed="Warm golden hour vibes"))
    await db.flush()

    repo = SettingsRepository(db)
    all_settings = await repo.get_all()
    assert all_settings.get("style_seed") == "Warm golden hour vibes"


def _make_test_token() -> str:
    return create_jwt_token(user_id="user-test-settings")


def test_get_settings_returns_200(client: TestClient):
    response = client.get(
        "/api/v1/settings",
        headers={"Authorization": f"Bearer {_make_test_token()}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "claudeApiKey" in data
    assert "sessionBudgetUsd" in data
    assert "styleSeed" in data


def test_patch_settings_updates_style_seed(client: TestClient):
    response = client.patch(
        "/api/v1/settings",
        json={"styleSeed": "Moody, dark cinematography"},
        headers={"Authorization": f"Bearer {_make_test_token()}"},
    )
    assert response.status_code == 200
    assert response.json()["styleSeed"] == "Moody, dark cinematography"


def test_settings_endpoint_requires_auth(unauthed_client: TestClient):
    response = unauthed_client.get("/api/v1/settings")
    assert response.status_code == 401
