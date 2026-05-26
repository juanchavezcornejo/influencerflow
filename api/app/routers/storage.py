"""Cloud storage integration endpoints."""

from __future__ import annotations

from http import HTTPStatus

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.integrations.google_drive import GoogleDriveClient, GoogleDriveOAuth
from app.lib.jwt_utils import decode_jwt_token
from app.repositories.storage import StorageCredentialsRepository

router = APIRouter(prefix="/storage", tags=["storage"])


def get_current_user_id(authorization: str | None = Header(None)) -> str:
    """Extract user_id from JWT token in Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED, detail="Missing Authorization header"
        )

    token = authorization[7:]  # Remove "Bearer " prefix
    payload = decode_jwt_token(token)
    if not payload:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Invalid token")

    return payload.get("user_id")


@router.get("/google/oauth/start")
async def start_google_oauth() -> dict:
    """Get Google OAuth consent URL."""
    try:
        auth_url = GoogleDriveOAuth.get_auth_url()
        return {"auth_url": auth_url}
    except Exception as e:
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.get("/google/oauth/callback")
async def google_oauth_callback(
    code: str = Query(...),
    db: AsyncSession = Depends(get_db),
    authorization: str | None = Header(None),
) -> dict:
    """Handle Google OAuth callback. Exchange code for tokens."""
    user_id = get_current_user_id(authorization)

    try:
        tokens = GoogleDriveOAuth.exchange_code_for_tokens(code)
        repo = StorageCredentialsRepository(db)
        _cred = await repo.upsert(
            user_id=user_id,
            provider="google_drive",
            refresh_token=tokens["refresh_token"],
            access_token=tokens["access_token"],
        )
        await db.commit()
        return {"provider": "google_drive", "email": ""}  # TODO: extract email from tokens
    except Exception as e:
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.get("/google/folders/{folder_id}")
async def get_google_folder_metadata(
    folder_id: str,
    db: AsyncSession = Depends(get_db),
    authorization: str | None = Header(None),
) -> dict:
    """Get folder metadata (name, file count preview)."""
    user_id = get_current_user_id(authorization)
    repo = StorageCredentialsRepository(db)
    cred = await repo.get_by_user_and_provider(user_id, "google_drive")

    if not cred:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED, detail="Not connected to Google Drive"
        )

    client = GoogleDriveClient(access_token=cred.access_token, refresh_token=cred.refresh_token)
    try:
        metadata = await client.get_folder_metadata(folder_id)
        return metadata
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail=f"Cannot access folder: {e}"
        ) from e


@router.delete("/google-drive")
async def disconnect_google_drive(
    db: AsyncSession = Depends(get_db),
    authorization: str | None = Header(None),
) -> dict:
    """Disconnect Google Drive and delete stored credentials."""
    user_id = get_current_user_id(authorization)
    repo = StorageCredentialsRepository(db)
    await repo.delete(user_id, "google_drive")
    await db.commit()
    return {"message": "Disconnected from Google Drive"}
