"""JWT token generation and validation."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt

from app.config import settings


def create_jwt_token(user_id: str, expires_in: timedelta = timedelta(days=7)) -> str:
    """Create a signed JWT token."""
    now = datetime.now(UTC)
    payload = {
        "user_id": user_id,
        "iat": now,
        "exp": now + expires_in,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_jwt_token(token: str) -> dict | None:
    """Decode and validate a JWT token. Returns payload or None if invalid."""
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.InvalidTokenError:
        return None
