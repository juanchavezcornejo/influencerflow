"""AI cache repository."""

from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_cache import AICache


class AICacheRepository:
    """Data access for AICache model."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, cache_key: str) -> dict | None:
        """Get cached response by key."""
        result = await self.db.execute(select(AICache).filter(AICache.cache_key == cache_key))
        cached = result.scalar_one_or_none()
        if cached:
            return json.loads(cached.response_json)
        return None

    async def set(
        self,
        cache_key: str,
        response: dict,
        model_used: str | None = None,
        tokens_in: int | None = None,
        tokens_out: int | None = None,
    ) -> AICache:
        """Store response in cache."""
        cached = AICache(
            cache_key=cache_key,
            response_json=json.dumps(response),
            model_used=model_used,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
        )
        self.db.add(cached)
        await self.db.flush()
        return cached

    async def invalidate_by_prefix(self, prefix: str) -> int:
        """Delete all cache entries with given prefix."""
        result = await self.db.execute(select(AICache).filter(AICache.cache_key.like(f"{prefix}%")))
        entries = result.scalars().all()
        count = len(entries)
        for entry in entries:
            await self.db.delete(entry)
        await self.db.flush()
        return count

    async def delete(self, cache_key: str) -> None:
        """Delete a specific cache entry."""
        result = await self.db.execute(select(AICache).filter(AICache.cache_key == cache_key))
        entry = result.scalar_one_or_none()
        if entry:
            await self.db.delete(entry)
            await self.db.flush()
