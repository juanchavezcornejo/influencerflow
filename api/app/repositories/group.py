"""Group repository."""

from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.group import Group, GroupAsset


class GroupRepository:
    """Data access for Group model."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, group_id: str) -> Group | None:
        result = await self.db.execute(select(Group).filter(Group.id == group_id))
        return result.scalar_one_or_none()

    async def get_by_session(self, session_id: str) -> list[Group]:
        result = await self.db.execute(
            select(Group).filter(Group.session_id == session_id).order_by(Group.order_index)
        )
        return result.scalars().all()

    async def create(
        self,
        session_id: str,
        name: str,
        auto_generated: bool = True,
        order_index: int | None = None,
    ) -> Group:
        # Get max order_index if not provided
        if order_index is None:
            result = await self.db.execute(
                select(Group)
                .filter(Group.session_id == session_id)
                .order_by(desc(Group.order_index))
                .limit(1)
            )
            last = result.scalar_one_or_none()
            order_index = (last.order_index + 1) if last else 0

        group = Group(
            session_id=session_id, name=name, auto_generated=auto_generated, order_index=order_index
        )
        self.db.add(group)
        await self.db.flush()
        return group

    async def update(self, group_id: str, **kwargs) -> Group | None:
        group = await self.get_by_id(group_id)
        if group:
            for key, value in kwargs.items():
                if hasattr(group, key):
                    setattr(group, key, value)
            await self.db.flush()
        return group

    async def delete(self, group_id: str) -> None:
        group = await self.get_by_id(group_id)
        if group:
            await self.db.delete(group)
            await self.db.flush()

    async def delete_by_session(self, session_id: str) -> None:
        """Delete all groups in a session (for Resync cleanup)."""
        result = await self.db.execute(select(Group).filter(Group.session_id == session_id))
        for group in result.scalars():
            await self.db.delete(group)
        await self.db.flush()


class GroupAssetRepository:
    """Data access for GroupAsset model."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_group(self, group_id: str) -> list[GroupAsset]:
        result = await self.db.execute(
            select(GroupAsset).filter(GroupAsset.group_id == group_id).order_by(GroupAsset.position)
        )
        return result.scalars().all()

    async def add_asset(self, group_id: str, asset_id: str, position: int) -> GroupAsset:
        ga = GroupAsset(group_id=group_id, asset_id=asset_id, position=position)
        self.db.add(ga)
        await self.db.flush()
        return ga

    async def remove_asset(self, group_id: str, asset_id: str) -> None:
        result = await self.db.execute(
            select(GroupAsset).filter(
                (GroupAsset.group_id == group_id) & (GroupAsset.asset_id == asset_id)
            )
        )
        ga = result.scalar_one_or_none()
        if ga:
            await self.db.delete(ga)
            await self.db.flush()

    async def reorder(self, group_id: str, asset_ids: list[str]) -> None:
        """Reorder assets in a group."""
        for position, asset_id in enumerate(asset_ids):
            result = await self.db.execute(
                select(GroupAsset).filter(
                    (GroupAsset.group_id == group_id) & (GroupAsset.asset_id == asset_id)
                )
            )
            ga = result.scalar_one_or_none()
            if ga:
                ga.position = position
            await self.db.flush()
