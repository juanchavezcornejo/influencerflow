"""Face crop repository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.face_crop import FaceCrop


class FaceCropRepository:
    """Data access for FaceCrop model."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, crop_id: str) -> FaceCrop | None:
        result = await self.db.execute(select(FaceCrop).filter(FaceCrop.id == crop_id))
        return result.scalar_one_or_none()

    async def get_by_asset(self, asset_id: str) -> list[FaceCrop]:
        result = await self.db.execute(select(FaceCrop).filter(FaceCrop.asset_id == asset_id))
        return result.scalars().all()

    async def create(
        self,
        asset_id: str,
        bbox_json: str,
        crop_path: str,
        landmarks_json: str | None = None,
    ) -> FaceCrop:
        crop = FaceCrop(
            asset_id=asset_id,
            bbox_json=bbox_json,
            crop_path=crop_path,
            landmarks_json=landmarks_json,
            status="cropped",
        )
        self.db.add(crop)
        await self.db.flush()
        return crop

    async def update(self, crop_id: str, **kwargs) -> FaceCrop | None:
        crop = await self.get_by_id(crop_id)
        if crop:
            for key, value in kwargs.items():
                if hasattr(crop, key):
                    setattr(crop, key, value)
            await self.db.flush()
        return crop

    async def delete(self, crop_id: str) -> None:
        crop = await self.get_by_id(crop_id)
        if crop:
            await self.db.delete(crop)
            await self.db.flush()
