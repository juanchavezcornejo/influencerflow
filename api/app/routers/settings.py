"""Settings router — GET/PATCH /settings."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.settings import SettingsPatch, SettingsResponse
from app.services.settings_service import SettingsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SettingsResponse)
async def get_settings(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> SettingsResponse:
    """Return current settings. Sensitive keys are masked in the response."""
    service = SettingsService(db)
    return await service.get()


@router.patch("", response_model=SettingsResponse)
async def patch_settings(
    patch: SettingsPatch,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> SettingsResponse:
    """Update one or more settings. Omitted fields are left unchanged."""
    service = SettingsService(db)
    result = await service.patch(patch)
    await db.commit()
    return result
