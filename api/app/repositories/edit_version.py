"""Edit version repository."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.edit_version import EditVersion


class EditVersionRepository:
    """Data access for EditVersion model."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, version_id: str) -> EditVersion | None:
        result = await self.db.execute(select(EditVersion).filter(EditVersion.id == version_id))
        return result.scalar_one_or_none()

    async def get_by_asset(self, asset_id: str) -> list[EditVersion]:
        result = await self.db.execute(
            select(EditVersion)
            .filter(EditVersion.asset_id == asset_id)
            .order_by(desc(EditVersion.created_at))
        )
        return result.scalars().all()

    async def get_current(self, asset_id: str) -> EditVersion | None:
        """Get current accepted version for asset (latest with user_decision=accepted)."""
        result = await self.db.execute(
            select(EditVersion)
            .filter((EditVersion.asset_id == asset_id) & (EditVersion.user_decision == "accepted"))
            .order_by(desc(EditVersion.created_at))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        asset_id: str,
        changes_log_text: str | None = None,
        corrections_applied_json: str | None = None,
        parent_version_id: str | None = None,
    ) -> EditVersion:
        version = EditVersion(
            asset_id=asset_id,
            changes_log_text=changes_log_text,
            corrections_applied_json=corrections_applied_json,
            parent_version_id=parent_version_id,
            created_at=datetime.now(),
        )
        self.db.add(version)
        await self.db.flush()
        return version

    async def update(self, version_id: str, **kwargs) -> EditVersion | None:
        version = await self.get_by_id(version_id)
        if version:
            for key, value in kwargs.items():
                if hasattr(version, key):
                    setattr(version, key, value)
            await self.db.flush()
        return version

    async def delete(self, version_id: str) -> None:
        version = await self.get_by_id(version_id)
        if version:
            await self.db.delete(version)
            await self.db.flush()
