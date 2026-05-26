"""Settings repository — key-value CRUD for app_settings table."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.settings import AppSetting


class SettingsRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(self) -> dict[str, str | None]:
        """Return all settings as {key: value} dict."""
        result = await self.db.execute(select(AppSetting))
        rows = result.scalars().all()
        return {row.key: row.value for row in rows}

    async def set(self, key: str, value: str | None) -> None:
        """Upsert a single setting. flush() but do not commit."""
        result = await self.db.execute(select(AppSetting).where(AppSetting.key == key))
        row = result.scalar_one_or_none()
        if row is None:
            row = AppSetting(key=key, value=value)
            self.db.add(row)
        else:
            row.value = value
        await self.db.flush()

    async def set_many(self, updates: dict[str, str | None]) -> None:
        """Upsert multiple settings in one call."""
        for key, value in updates.items():
            await self.set(key, value)
