#!/usr/bin/env python3
"""Seed a single user account (MVP: single-user only).

Usage:
    SINGLE_USER_EMAIL=juan@example.com SINGLE_USER_PASSWORD=mysecret uv run python scripts/seed_user.py

Idempotent: running twice does not create duplicates.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import bcrypt
from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import AsyncSessionLocal
from app.models.user import User


async def seed_user() -> None:
    """Seed a single user if not already present."""
    email = os.getenv("SINGLE_USER_EMAIL")
    password = os.getenv("SINGLE_USER_PASSWORD")

    if not email or not password:
        print("ERROR: SINGLE_USER_EMAIL and SINGLE_USER_PASSWORD env vars required")
        sys.exit(1)

    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode(
        "utf-8"
    )

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).filter(User.email == email))
        existing = result.scalar_one_or_none()

        if existing:
            print(f"✓ User {email} already exists")
            return

        user = User(email=email, password_hash=password_hash)
        session.add(user)
        await session.commit()
        print(f"✓ Created user {email}")


if __name__ == "__main__":
    asyncio.run(seed_user())
