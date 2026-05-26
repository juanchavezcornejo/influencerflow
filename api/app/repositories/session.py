"""Session repository."""

from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import Session


class SessionRepository:
    """Data access for Session model."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, session_id: str) -> Session | None:
        result = await self.db.execute(select(Session).filter(Session.id == session_id))
        return result.scalar_one_or_none()

    async def get_by_user(self, user_id: str, limit: int = 100) -> list[Session]:
        result = await self.db.execute(
            select(Session)
            .filter(Session.user_id == user_id)
            .order_by(desc(Session.created_at))
            .limit(limit)
        )
        return result.scalars().all()

    async def create(
        self, user_id: str, cloud_provider: str, cloud_folder_id: str, cloud_folder_name: str
    ) -> Session:
        session = Session(
            user_id=user_id,
            cloud_provider=cloud_provider,
            cloud_folder_id=cloud_folder_id,
            cloud_folder_name=cloud_folder_name,
        )
        self.db.add(session)
        await self.db.flush()
        return session

    async def update_status(self, session_id: str, status: str) -> Session | None:
        session = await self.get_by_id(session_id)
        if session:
            session.status = status
            await self.db.flush()
        return session

    async def mark_deleted(self, session_id: str) -> None:
        session = await self.get_by_id(session_id)
        if session:
            session.status = "deleted"
            await self.db.flush()
