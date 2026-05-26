"""Asset endpoints (preview/thumbnail serving, etc.)."""

from __future__ import annotations

from http import HTTPStatus
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.asset import Asset
from app.models.group import GroupAsset
from app.repositories.asset import AssetRepository
from app.repositories.session import SessionRepository
from app.routers.storage import get_current_user_id

router = APIRouter(prefix="/assets", tags=["assets"])


class UpdateAssetRequest(BaseModel):
    """Request to update asset fields."""

    status: str | None = None


class AssetResponse(BaseModel):
    """Asset response."""

    id: str
    original_filename: str
    phash: str | None
    has_face: bool
    is_video: bool
    status: str
    near_duplicate_cluster_id: str | None


@router.get("/{asset_id}/thumbnail")
async def get_thumbnail(
    asset_id: str,
    db: AsyncSession = Depends(get_db),
    authorization: str | None = None,
) -> FileResponse:
    """Stream thumbnail preview."""
    # TODO: verify user owns the session containing this asset
    repo = AssetRepository(db)
    asset = await repo.get_by_id(asset_id)

    if not asset or not asset.thumbnail_path:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Thumbnail not found")

    path = Path(asset.thumbnail_path)
    if not path.exists():
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="File not found")

    return FileResponse(
        path,
        media_type="image/jpeg",
        headers={"Cache-Control": "private, max-age=3600"},
    )


@router.get("/{asset_id}/preview")
async def get_preview(
    asset_id: str,
    db: AsyncSession = Depends(get_db),
    authorization: str | None = None,
) -> FileResponse:
    """Stream preview image."""
    repo = AssetRepository(db)
    asset = await repo.get_by_id(asset_id)

    if not asset or not asset.preview_path:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Preview not found")

    path = Path(asset.preview_path)
    if not path.exists():
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="File not found")

    return FileResponse(
        path,
        media_type="image/jpeg",
        headers={"Cache-Control": "private, max-age=3600"},
    )


@router.patch("/{asset_id}")
async def update_asset(
    asset_id: str,
    body: UpdateAssetRequest,
    db: AsyncSession = Depends(get_db),
    authorization: str | None = None,
) -> dict:
    """Update asset fields (status, etc)."""
    get_current_user_id(authorization)  # Auth check
    repo = AssetRepository(db)
    asset = await repo.get_by_id(asset_id)

    if not asset:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND)

    updates = {}
    if body.status is not None:
        updates["status"] = body.status

    if updates:
        await repo.update(asset_id, **updates)
        await db.commit()

    return {"message": "Updated"}


@router.get("/session/{session_id}/ungrouped")
async def get_ungrouped_assets(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    authorization: str | None = None,
) -> list[AssetResponse]:
    """Get assets not in any group for a session."""
    user_id = get_current_user_id(authorization)

    # Verify session ownership
    session_repo = SessionRepository(db)
    session = await session_repo.get_by_id(session_id)
    if not session or session.user_id != user_id:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED)

    # Get all assets in session
    result = await db.execute(select(Asset).filter(Asset.session_id == session_id))
    all_assets = result.scalars().all()

    # Get all grouped asset IDs
    grouped_result = await db.execute(select(GroupAsset.asset_id))
    grouped_ids = set(grouped_result.scalars().all())

    # Filter ungrouped assets
    ungrouped = [a for a in all_assets if a.id not in grouped_ids]

    return [
        AssetResponse(
            id=asset.id,
            original_filename=asset.original_filename,
            phash=asset.phash,
            has_face=asset.has_face,
            is_video=asset.is_video,
            status=asset.status,
            near_duplicate_cluster_id=asset.near_duplicate_cluster_id,
        )
        for asset in ungrouped
    ]
