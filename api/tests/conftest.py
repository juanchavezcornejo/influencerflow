"""Shared test fixtures."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator, Iterator

from cryptography.fernet import Fernet

# Must be set BEFORE app.config.Settings() is instantiated via the app import.
os.environ.setdefault("FERNET_KEY", Fernet.generate_key().decode())
os.environ.setdefault("JWT_SECRET", "test-secret-key")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool

from app.workers.celery_app import celery_app


def _override_get_current_user():
    """Return a stub User so tests never hit the DB for auth."""
    from app.models.user import User

    return User(id="user-test-settings", email="test@test.com", password_hash="x")


@pytest.fixture
def client() -> Iterator[TestClient]:
    """FastAPI TestClient with the real app instance backed by in-memory SQLite.

    Imports app.main lazily so that the face_recognition SystemExit
    only fires when this fixture is actually requested, not at collection time.
    """
    import asyncio

    from app.db import Base, get_db
    from app.dependencies import get_current_user
    from app.main import app

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async def _create_tables() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.get_event_loop().run_until_complete(_create_tables())

    async def override_get_db() -> AsyncIterator[AsyncSession]:
        async with AsyncSession(engine, expire_on_commit=False) as session:
            yield session

    app.dependency_overrides[get_current_user] = _override_get_current_user
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_db, None)

    asyncio.get_event_loop().run_until_complete(engine.dispose())


@pytest.fixture
def unauthed_client() -> Iterator[TestClient]:
    """FastAPI TestClient with no auth override — tests real 401 behaviour."""
    import asyncio

    from app.db import Base, get_db
    from app.main import app

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async def _create_tables() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.get_event_loop().run_until_complete(_create_tables())

    async def override_get_db() -> AsyncIterator[AsyncSession]:
        async with AsyncSession(engine, expire_on_commit=False) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.pop(get_db, None)
    asyncio.get_event_loop().run_until_complete(engine.dispose())


@pytest.fixture(autouse=True)
def _celery_eager_mode() -> Iterator[None]:
    """Run Celery tasks inline during tests (no broker needed)."""
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True
    yield
    celery_app.conf.task_always_eager = False
    celery_app.conf.task_eager_propagates = False
