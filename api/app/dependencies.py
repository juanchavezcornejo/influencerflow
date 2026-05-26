"""Dependency injection for FastAPI."""

from http import HTTPStatus

from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import RuntimeSettings, settings
from app.db import get_db
from app.lib.jwt_utils import decode_jwt_token
from app.models.user import User
from app.repositories.user import UserRepository


async def get_current_user(
    authorization: str | None = Header(None),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and validate current user from Authorization header (Bearer token)."""
    if not authorization:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="No authorization header")

    # Remove "Bearer " prefix if present
    token = (
        authorization.replace("Bearer ", "")
        if authorization.startswith("Bearer ")
        else authorization
    )

    payload = decode_jwt_token(token)
    if not payload or "user_id" not in payload:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Invalid or expired token")

    user_id = payload["user_id"]
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)

    if not user:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="User not found")

    return user


async def get_runtime_settings(db: AsyncSession = Depends(get_db)) -> RuntimeSettings:
    """FastAPI dependency: merges DB app_settings with env defaults."""
    from app.services.settings_service import SettingsService

    svc = SettingsService(db)
    effective = await svc.get_effective()
    return RuntimeSettings(
        anthropic_api_key=effective.claude_api_key or "",
        replicate_api_token=effective.replicate_api_key or "",
        google_oauth_client_id=effective.google_client_id or "",
        google_oauth_client_secret=effective.google_client_secret or "",
        google_oauth_redirect_uri=settings.google_oauth_redirect_uri,
        session_budget_usd=float(effective.session_budget_usd or 10.0),
        session_hard_cap_usd=float(effective.session_hard_cap_usd or 50.0),
        style_seed_text=effective.style_seed or "",
    )
