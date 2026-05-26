"""Group management endpoints."""

from __future__ import annotations

from http import HTTPStatus

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.repositories.asset import AssetRepository
from app.repositories.group import GroupAssetRepository, GroupRepository
from app.repositories.session import SessionRepository
from app.routers.storage import get_current_user_id
from app.services.grouping_service import GroupingService

router = APIRouter(prefix="/groups", tags=["groups"])


class CreateGroupRequest(BaseModel):
    """Request to create a new group."""

    session_id: str
    name: str


class GroupResponse(BaseModel):
    """Group response."""

    id: str
    session_id: str
    name: str
    auto_generated: bool
    asset_count: int
    order_index: int


class AssetInGroupResponse(BaseModel):
    """Asset in group response."""

    id: str
    original_filename: str
    phash: str | None
    has_face: bool
    is_video: bool
    status: str
    near_duplicate_cluster_id: str | None


class GroupDetailResponse(GroupResponse):
    """Group with nested assets."""

    assets: list[AssetInGroupResponse]


@router.get("/session/{session_id}/groups", response_model=list[GroupDetailResponse])
async def get_session_groups(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    authorization: str | None = Header(None),
) -> list[GroupDetailResponse]:
    """Get all groups in a session with nested assets."""
    user_id = get_current_user_id(authorization)

    # Verify session ownership
    session_repo = SessionRepository(db)
    session = await session_repo.get_by_id(session_id)
    if not session or session.user_id != user_id:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED)

    group_repo = GroupRepository(db)
    group_asset_repo = GroupAssetRepository(db)
    asset_repo = AssetRepository(db)

    groups = await group_repo.get_by_session(session_id)
    result = []

    for group in groups:
        gas = await group_asset_repo.get_by_group(group.id)
        assets = []

        for ga in gas:
            asset = await asset_repo.get_by_id(ga.asset_id)
            if asset:
                assets.append(
                    AssetInGroupResponse(
                        id=asset.id,
                        original_filename=asset.original_filename,
                        phash=asset.phash,
                        has_face=asset.has_face,
                        is_video=asset.is_video,
                        status=asset.status,
                        near_duplicate_cluster_id=asset.near_duplicate_cluster_id,
                    )
                )

        result.append(
            GroupDetailResponse(
                id=group.id,
                session_id=group.session_id,
                name=group.name,
                auto_generated=group.auto_generated,
                asset_count=len(assets),
                order_index=group.order_index,
                assets=assets,
            )
        )

    return result


@router.post("/session/{session_id}/groups/regroup-deterministic")
async def regroup_deterministic(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    authorization: str | None = Header(None),
) -> dict:
    """Re-run deterministic grouping (free operation)."""
    user_id = get_current_user_id(authorization)

    session_repo = SessionRepository(db)
    session = await session_repo.get_by_id(session_id)
    if not session or session.user_id != user_id:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED)

    service = GroupingService(db)
    await service.regroup_deterministic(session_id, session.cloud_folder_name)
    await db.commit()

    return {"message": "Regrouped"}


@router.post("")
async def create_group(
    body: CreateGroupRequest,
    db: AsyncSession = Depends(get_db),
    authorization: str | None = Header(None),
) -> GroupResponse:
    """Create an empty group."""
    user_id = get_current_user_id(authorization)

    # Verify session ownership
    session_repo = SessionRepository(db)
    session = await session_repo.get_by_id(body.session_id)
    if not session or session.user_id != user_id:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED)

    group_repo = GroupRepository(db)
    group = await group_repo.create(body.session_id, body.name, auto_generated=False)
    await db.commit()

    return GroupResponse(
        id=group.id,
        session_id=group.session_id,
        name=group.name,
        auto_generated=group.auto_generated,
        asset_count=0,
        order_index=group.order_index,
    )


@router.patch("/{group_id}")
async def update_group(
    group_id: str,
    name: str | None = None,
    order_index: int | None = None,
    db: AsyncSession = Depends(get_db),
    authorization: str | None = Header(None),
) -> GroupResponse:
    """Update group name or order."""
    get_current_user_id(authorization)  # Auth check
    group_repo = GroupRepository(db)
    group = await group_repo.get_by_id(group_id)

    if not group:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND)

    updates = {}
    if name is not None:
        updates["name"] = name
    if order_index is not None:
        updates["order_index"] = order_index

    group = await group_repo.update(group_id, **updates)
    await db.commit()

    group_asset_repo = GroupAssetRepository(db)
    gas = await group_asset_repo.get_by_group(group_id)

    return GroupResponse(
        id=group.id,
        session_id=group.session_id,
        name=group.name,
        auto_generated=group.auto_generated,
        asset_count=len(gas),
        order_index=group.order_index,
    )


@router.delete("/{group_id}")
async def delete_group(
    group_id: str,
    db: AsyncSession = Depends(get_db),
    authorization: str | None = Header(None),
) -> dict:
    """Delete a group (assets return to ungrouped pool)."""
    get_current_user_id(authorization)
    group_repo = GroupRepository(db)

    group = await group_repo.get_by_id(group_id)
    if not group:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND)

    # Delete all group_assets associations
    group_asset_repo = GroupAssetRepository(db)
    gas = await group_asset_repo.get_by_group(group_id)
    for ga in gas:
        await db.delete(ga)

    # Delete group
    await group_repo.delete(group_id)
    await db.commit()

    return {"message": "Group deleted"}


@router.post("/{group_id}/assets/{asset_id}")
async def add_asset_to_group(
    group_id: str,
    asset_id: str,
    position: int = 0,
    db: AsyncSession = Depends(get_db),
    authorization: str | None = Header(None),
) -> dict:
    """Add an asset to a group at a position."""
    get_current_user_id(authorization)
    group_repo = GroupRepository(db)
    group = await group_repo.get_by_id(group_id)

    if not group:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND)

    group_asset_repo = GroupAssetRepository(db)
    await group_asset_repo.add_asset(group_id, asset_id, position)
    await db.commit()

    return {"message": "Asset added"}


@router.delete("/{group_id}/assets/{asset_id}")
async def remove_asset_from_group(
    group_id: str,
    asset_id: str,
    db: AsyncSession = Depends(get_db),
    authorization: str | None = Header(None),
) -> dict:
    """Remove an asset from a group."""
    get_current_user_id(authorization)
    group_asset_repo = GroupAssetRepository(db)
    await group_asset_repo.remove_asset(group_id, asset_id)
    await db.commit()

    return {"message": "Asset removed"}


@router.patch("/{group_id}/assets/reorder")
async def reorder_assets(
    group_id: str,
    asset_ids: list[str],
    db: AsyncSession = Depends(get_db),
    authorization: str | None = Header(None),
) -> dict:
    """Reorder assets in a group."""
    get_current_user_id(authorization)
    group_asset_repo = GroupAssetRepository(db)
    await group_asset_repo.reorder(group_id, asset_ids)
    await db.commit()

    return {"message": "Reordered"}


class MoveAssetRequest(BaseModel):
    """Request to move an asset to a group."""

    from_group_id: str | None = None
    position: int = 0


@router.post("/{group_id}/assets/{asset_id}/move")
async def move_asset_to_group(
    group_id: str,
    asset_id: str,
    body: MoveAssetRequest,
    db: AsyncSession = Depends(get_db),
    authorization: str | None = Header(None),
) -> dict:
    """Move an asset from one group to another."""
    get_current_user_id(authorization)
    group_asset_repo = GroupAssetRepository(db)

    # Remove from old group if specified
    if body.from_group_id:
        await group_asset_repo.remove_asset(body.from_group_id, asset_id)

    # Add to new group at position
    await group_asset_repo.add_asset(group_id, asset_id, body.position)
    await db.commit()

    return {"message": "Asset moved"}


@router.patch("")
async def reorder_groups(
    group_ids: list[str],
    db: AsyncSession = Depends(get_db),
    authorization: str | None = Header(None),
) -> dict:
    """Reorder groups in a session."""
    get_current_user_id(authorization)
    group_repo = GroupRepository(db)

    for order_index, group_id in enumerate(group_ids):
        await group_repo.update(group_id, order_index=order_index)
        await db.flush()

    await db.commit()
    return {"message": "Groups reordered"}
