"""Storage credentials repository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.storage import StorageCredentials


class StorageCredentialsRepository:
    """Data access for StorageCredentials model."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_user_and_provider(
        self, user_id: str, provider: str
    ) -> StorageCredentials | None:
        result = await self.db.execute(
            select(StorageCredentials).filter(
                (StorageCredentials.user_id == user_id) & (StorageCredentials.provider == provider)
            )
        )
        return result.scalar_one_or_none()

    async def upsert(
        self, user_id: str, provider: str, refresh_token: str, access_token: str | None = None
    ) -> StorageCredentials:
        existing = await self.get_by_user_and_provider(user_id, provider)
        if existing:
            existing.refresh_token = refresh_token
            existing.access_token = access_token
            await self.db.flush()
            return existing

        cred = StorageCredentials(
            user_id=user_id,
            provider=provider,
            refresh_token=refresh_token,
            access_token=access_token,
        )
        self.db.add(cred)
        await self.db.flush()
        return cred

    async def delete(self, user_id: str, provider: str) -> None:
        cred = await self.get_by_user_and_provider(user_id, provider)
        if cred:
            await self.db.delete(cred)
            await self.db.flush()
