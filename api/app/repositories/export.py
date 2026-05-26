"""Repository for exports."""

from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.export import Export


class ExportRepository:
    """CRUD operations for exports."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        session_id: str,
        group_id: str,
    ) -> Export:
        """Create a new export job."""
        export = Export(
            session_id=session_id,
            group_id=group_id,
            status="pending",
            created_at=datetime.now(UTC),
        )
        self.session.add(export)
        await self.session.flush()
        return export

    async def get_by_id(self, export_id: str) -> Export | None:
        """Get export by ID."""
        result = await self.session.execute(select(Export).where(Export.id == export_id))
        return result.scalar_one_or_none()

    async def get_by_group(self, group_id: str) -> list[Export]:
        """Get all exports for a group, newest first."""
        result = await self.session.execute(
            select(Export).where(Export.group_id == group_id).order_by(Export.created_at.desc())
        )
        return result.scalars().all()

    async def update_status(
        self, export_id: str, status: str, zip_path: str | None = None
    ) -> Export | None:
        """Update export status and optionally zip_path."""
        await self.session.execute(
            update(Export)
            .where(Export.id == export_id)
            .values(
                status=status,
                zip_path=zip_path,
                completed_at=datetime.now(UTC) if status != "pending" else None,
            )
        )
        await self.session.flush()
        return await self.get_by_id(export_id)
