"""E2E test app factory — creates a FastAPI app with mocked external services.

Usage:
    python api/app/testing/e2e_app.py
    uvicorn api.app.testing.e2e_app:app --port 8000
"""

from __future__ import annotations

import bcrypt
from fastapi import FastAPI
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy import select

from app import __version__
from app.db import AsyncSessionLocal, Base, engine
from app.models.user import User
from app.routers import (
    assets,
    auth,
    cost,
    descriptions,
    edits,
    events,
    exports,
    face_crops,
    groups,
    health,
    sessions,
    storage,
)
from app.routers import settings as settings_router

from .mocks import (
    MockClaudeClient,
    MockGoogleDriveClient,
    MockGoogleDriveOAuth,
    MockReplicateClient,
)

API_V1_PREFIX = "/api/v1"


def _apply_mock_patches() -> None:
    """Monkey-patch external integrations with mock versions."""
    import app.integrations.claude as claude_mod
    import app.integrations.google_drive as drive_mod
    import app.integrations.replicate as replicate_mod
    import app.routers.storage as storage_router_mod
    import app.services.description_service as desc_service

    drive_mod.GoogleDriveClient = MockGoogleDriveClient
    drive_mod.GoogleDriveOAuth = MockGoogleDriveOAuth
    claude_mod.ClaudeClient = MockClaudeClient
    replicate_mod.ReplicateClient = MockReplicateClient

    # Patch router module's reference (imported at module level before our patch)
    storage_router_mod.GoogleDriveClient = MockGoogleDriveClient
    storage_router_mod.GoogleDriveOAuth = MockGoogleDriveOAuth

    if hasattr(desc_service, "ClaudeClient"):
        desc_service.ClaudeClient = MockClaudeClient


async def _seed_e2e_user() -> None:
    """Ensure test user exists on startup (idempotent)."""
    email = "e2e@test.com"
    password = "e2e-test-password"

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).filter(User.email == email))
        existing = result.scalar_one_or_none()
        if existing:
            return

        password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode(
            "utf-8"
        )
        user = User(email=email, password_hash=password_hash)
        session.add(user)
        await session.commit()


def create_e2e_app() -> FastAPI:
    """Create FastAPI app with all external services mocked."""
    _apply_mock_patches()

    limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])

    app = FastAPI(
        title="InfluencerFlow API (E2E)",
        version=__version__,
        docs_url="/api/v1/docs",
        redoc_url=None,
        openapi_url="/api/v1/openapi.json",
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    @app.on_event("startup")
    async def startup() -> None:
        await _seed_e2e_user()

    app.include_router(health.router, prefix=API_V1_PREFIX)
    app.include_router(auth.router, prefix=API_V1_PREFIX)
    app.include_router(storage.router, prefix=API_V1_PREFIX)
    app.include_router(sessions.router, prefix=API_V1_PREFIX)
    app.include_router(assets.router, prefix=API_V1_PREFIX)
    app.include_router(events.router, prefix=API_V1_PREFIX)
    app.include_router(groups.router, prefix=API_V1_PREFIX)
    app.include_router(edits.router, prefix=API_V1_PREFIX)
    app.include_router(cost.router, prefix=API_V1_PREFIX)
    app.include_router(face_crops.router, prefix=API_V1_PREFIX)
    app.include_router(descriptions.router)
    app.include_router(exports.router)
    app.include_router(settings_router.router, prefix=API_V1_PREFIX)

    return app


app = create_e2e_app()
