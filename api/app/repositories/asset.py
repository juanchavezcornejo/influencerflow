"""Asset repository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset


class AssetRepository:
    """Data access for Asset model."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, asset_id: str) -> Asset | None:
        result = await self.db.execute(select(Asset).filter(Asset.id == asset_id))
        return result.scalar_one_or_none()

    async def get_by_session(self, session_id: str) -> list[Asset]:
        result = await self.db.execute(
            select(Asset).filter(Asset.session_id == session_id).order_by(Asset.taken_at)
        )
        return result.scalars().all()

    async def create(
        self,
        session_id: str,
        original_cloud_path: str,
        original_filename: str,
        is_video: bool = False,
    ) -> Asset:
        asset = Asset(
            session_id=session_id,
            original_cloud_path=original_cloud_path,
            original_filename=original_filename,
            is_video=is_video,
        )
        self.db.add(asset)
        await self.db.flush()
        return asset

    async def update(self, asset_id: str, **kwargs) -> Asset | None:
        asset = await self.get_by_id(asset_id)
        if asset:
            for key, value in kwargs.items():
                if hasattr(asset, key):
                    setattr(asset, key, value)
            await self.db.flush()
        return asset

    async def delete_by_session(self, session_id: str) -> None:
        """Delete all assets in a session (used during Resync)."""
        result = await self.db.execute(select(Asset).filter(Asset.session_id == session_id))
        for asset in result.scalars():
            await self.db.delete(asset)
        await self.db.flush()
