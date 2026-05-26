"""FastAPI application factory + ASGI entrypoint."""

from __future__ import annotations

from fastapi import FastAPI
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app import __version__
from app.config import settings
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

API_V1_PREFIX = "/api/v1"

limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])


def create_app() -> FastAPI:
    app = FastAPI(
        title="InfluencerFlow API",
        version=__version__,
        docs_url="/api/v1/docs" if settings.is_development else None,
        redoc_url=None,
        openapi_url="/api/v1/openapi.json" if settings.is_development else None,
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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


app = create_app()
