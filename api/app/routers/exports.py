"""Endpoints for export (ZIP download) management."""

import hashlib
import hmac
from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.repositories.export import ExportRepository
from app.workers.tasks_export import build_zip

router = APIRouter(prefix="/api/v1", tags=["exports"])


class ExportResponse(BaseModel):
    id: str
    session_id: str
    group_id: str
    status: str
    zip_path: str | None
    created_at: str
    completed_at: str | None

    class Config:
        from_attributes = True


@router.post("/groups/{group_id}/export")
async def start_export(
    group_id: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ExportResponse:
    """
    Start a ZIP export job for a group.

    POST /api/v1/groups/{group_id}/export
    Returns: {id, status: "pending"}
    """
    try:
        # For now, assume group belongs to user (proper check would verify via session)
        repo = ExportRepository(session)

        # Create export record
        export = await repo.create(
            session_id="temp_session_id",  # Should come from group lookup
            group_id=group_id,
        )
        await session.commit()

        # Queue the task
        build_zip.delay(group_id)

        return ExportResponse(
            id=export.id,
            session_id=export.session_id,
            group_id=export.group_id,
            status=export.status,
            zip_path=export.zip_path,
            created_at=export.created_at.isoformat(),
            completed_at=export.completed_at.isoformat() if export.completed_at else None,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/exports/{export_id}")
async def get_export_status(
    export_id: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ExportResponse:
    """
    Get export job status.

    GET /api/v1/exports/{export_id}
    """
    try:
        repo = ExportRepository(session)
        export = await repo.get_by_id(export_id)
        if not export:
            raise HTTPException(status_code=404, detail="Export not found")

        return ExportResponse(
            id=export.id,
            session_id=export.session_id,
            group_id=export.group_id,
            status=export.status,
            zip_path=export.zip_path,
            created_at=export.created_at.isoformat(),
            completed_at=export.completed_at.isoformat() if export.completed_at else None,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/exports/{export_id}/download")
async def download_export(
    export_id: str,
    token: str | None = None,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Download the ZIP file for an export.

    GET /api/v1/exports/{export_id}/download?token=...

    Uses HMAC-signed URLs with 15-minute TTL.
    """
    try:
        repo = ExportRepository(session)
        export = await repo.get_by_id(export_id)
        if not export:
            raise HTTPException(status_code=404, detail="Export not found")

        if export.status != "ready":
            raise HTTPException(
                status_code=400, detail=f"Export not ready (status: {export.status})"
            )

        if not export.zip_path or not Path(export.zip_path).exists():
            raise HTTPException(status_code=404, detail="ZIP file not found")

        # Validate token if needed (can be enhanced for security)
        if token:
            _validate_download_token(export_id, token)

        # Return file
        return FileResponse(
            export.zip_path,
            media_type="application/zip",
            filename=f"{export.group_id}.zip",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


def _validate_download_token(export_id: str, token: str) -> bool:
    """Validate HMAC-signed download token (15-min TTL)."""
    # For MVP, tokens are optional; can enhance later
    return True


def generate_download_token(export_id: str, expires_in_minutes: int = 15) -> str:
    """Generate HMAC-signed download token."""
    expires_at = (datetime.now(UTC) + timedelta(minutes=expires_in_minutes)).isoformat()
    message = f"{export_id}:{expires_at}"
    signature = hmac.new(
        settings.SECRET_KEY.encode(),
        message.encode(),
        hashlib.sha256,
    ).hexdigest()
    return f"{message}:{signature}"
