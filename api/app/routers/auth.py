"""Authentication endpoints."""

from __future__ import annotations

from http import HTTPStatus

import bcrypt
from fastapi import APIRouter, Body, Depends, HTTPException, Request, Response
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.lib.jwt_utils import create_jwt_token, decode_jwt_token
from app.repositories.user import UserRepository
from app.schemas.auth import AuthResponse, LoginRequest, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/login", response_model=AuthResponse)
@limiter.limit("5/15 minutes")
async def login(
    request: Request,
    body: LoginRequest = Body(),
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    """Login with email + password. Returns JWT token."""
    repo = UserRepository(db)
    user = await repo.get_by_email(body.email)

    if not user or not bcrypt.checkpw(
        body.password.encode("utf-8"), user.password_hash.encode("utf-8")
    ):
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Invalid email or password")

    token = create_jwt_token(user.id)
    return AuthResponse(accessToken=token)


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    token: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Get current user info from JWT token (from Authorization header or cookie)."""
    if not token:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="No token provided")

    payload = decode_jwt_token(token)
    if not payload:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Invalid or expired token")

    user_id = payload.get("user_id")
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)

    if not user:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="User not found")

    return UserResponse(id=user.id, email=user.email)


@router.post("/logout")
async def logout(response: Response) -> dict:
    """Logout (clears session/cookie on client)."""
    response.delete_cookie("Authorization")
    return {"message": "logged out"}
