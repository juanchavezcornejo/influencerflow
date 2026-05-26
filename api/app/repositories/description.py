"""Repository for descriptions."""

from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.description import Description


class DescriptionRepository:
    """CRUD operations for descriptions."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        group_id: str,
        text: str,
        custom_prompt: str | None = None,
        model_used: str | None = None,
        tokens_in: int | None = None,
        tokens_out: int | None = None,
    ) -> Description:
        """Create a new description."""
        desc = Description(
            group_id=group_id,
            text=text,
            custom_prompt=custom_prompt,
            model_used=model_used,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            is_current=True,
            created_at=datetime.now(UTC),
        )
        self.session.add(desc)
        await self.session.flush()
        return desc

    async def get_by_id(self, desc_id: str) -> Description | None:
        """Get description by ID."""
        result = await self.session.execute(select(Description).where(Description.id == desc_id))
        return result.scalar_one_or_none()

    async def get_by_group(self, group_id: str) -> list[Description]:
        """Get all descriptions for a group, newest first."""
        result = await self.session.execute(
            select(Description)
            .where(Description.group_id == group_id)
            .order_by(Description.created_at.desc())
        )
        return result.scalars().all()

    async def get_current_by_group(self, group_id: str) -> Description | None:
        """Get the current (is_current=true) description for a group."""
        result = await self.session.execute(
            select(Description)
            .where(Description.group_id == group_id, Description.is_current.is_(True))
            .order_by(Description.created_at.desc())
        )
        return result.scalar_one_or_none()

    async def set_current(self, group_id: str, desc_id: str) -> Description | None:
        """Set a description as current and unset others for the group."""
        # Unset all others
        await self.session.execute(
            update(Description)
            .where(Description.group_id == group_id, Description.id != desc_id)
            .values(is_current=False)
        )
        # Set this one
        await self.session.execute(
            update(Description).where(Description.id == desc_id).values(is_current=True)
        )
        await self.session.flush()
        return await self.get_by_id(desc_id)

    async def delete(self, desc_id: str) -> bool:
        """Delete a description."""
        desc = await self.get_by_id(desc_id)
        if desc:
            await self.session.delete(desc)
            await self.session.flush()
            return True
        return False
