"""Authentication schemas."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """Login credentials."""

    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    """Auth response with token."""

    accessToken: str


class UserResponse(BaseModel):
    """User profile response."""

    id: str
    email: str
