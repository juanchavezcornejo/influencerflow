# PATTERNS.md — Test Patterns and Recipes

Copy-paste recipes for common testing patterns in InfluencerFlow. All examples are based on the actual codebase.

---

## conftest.py Structure

`api/tests/conftest.py` currently provides two fixtures:

```python
"""Shared test fixtures."""

from __future__ import annotations
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.workers.celery_app import celery_app


@pytest.fixture
def client() -> Iterator[TestClient]:
    """FastAPI TestClient with the real app instance."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def _celery_eager_mode() -> Iterator[None]:
    """Run Celery tasks inline during tests (no broker needed)."""
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True
    yield
    celery_app.conf.task_always_eager = False
    celery_app.conf.task_eager_propagates = False
```

`_celery_eager_mode` is `autouse=True` — it applies to every test automatically. `client` must be requested explicitly.

---

## Adding a DB Fixture

Use this pattern for tests that need a real database. It creates all tables before the test and drops them after, giving each test a clean slate.

```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db import Base


@pytest.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    """In-memory SQLite DB for fast service tests.
    
    For Postgres-specific features (JSONB operators, partial indexes),
    use a real test database instead:
        engine = create_async_engine(os.environ["TEST_DATABASE_URL"])
    """
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
```

For per-test rollback instead of drop/create (faster for many tests):

```python
@pytest.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", ...)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with engine.connect() as conn:
        await conn.begin()
        async with AsyncSession(bind=conn, expire_on_commit=False) as session:
            yield session
        await conn.rollback()  # per-test rollback

    await engine.dispose()
```

---

## Fixture Factories

Factory helpers that create valid model instances. Based on the actual `Session` and `Asset` models from `001_initial_schema.py` and `test_grouping_service.py`.

```python
import uuid
from datetime import datetime, timezone

from app.models.session import Session
from app.models.asset import Asset


def make_session(
    *,
    id: str | None = None,
    user_id: str = "user-1",
    cloud_folder_id: str = "folder-1",
    cloud_folder_name: str = "Test Trip",
    cloud_provider: str = "google_drive",
    status: str = "ready",
) -> Session:
    return Session(
        id=id or str(uuid.uuid4()),
        user_id=user_id,
        cloud_folder_id=cloud_folder_id,
        cloud_folder_name=cloud_folder_name,
        cloud_provider=cloud_provider,
        status=status,
    )


def make_asset(
    *,
    session_id: str,
    id: str | None = None,
    original_filename: str = "IMG_0001.jpg",
    original_cloud_path: str = "photos/IMG_0001.jpg",
    taken_at: datetime | None = None,
    gps_lat: float | None = None,
    gps_lng: float | None = None,
    is_video: bool = False,
    has_face: bool = False,
    status: str = "active",
) -> Asset:
    return Asset(
        id=id or str(uuid.uuid4()),
        session_id=session_id,
        original_filename=original_filename,
        original_cloud_path=original_cloud_path,
        taken_at=taken_at or datetime(2024, 6, 15, 10, 0, 0, tzinfo=timezone.utc),
        gps_lat=gps_lat,
        gps_lng=gps_lng,
        is_video=is_video,
        has_face=has_face,
        status=status,
    )
```

Usage in a test:

```python
async def test_something(db: AsyncSession) -> None:
    session = make_session()
    db.add(session)
    await db.flush()

    asset = make_asset(session_id=session.id, gps_lat=40.71, gps_lng=-74.00)
    db.add(asset)
    await db.commit()
```

---

## Mocking External APIs

Use `AsyncMock` with `unittest.mock.patch` to prevent real Claude or Replicate calls. Patch at the call site (where it is used), not where it is defined.

```python
from unittest.mock import AsyncMock, patch


async def test_description_generated(db: AsyncSession) -> None:
    fake_response = {
        "text": "Golden hour in New York. Every shot tells a story. #travel #nyc",
        "tokens_in": 1200,
        "tokens_out": 80,
        "dollars_cost": 0.012,
    }

    with patch(
        "app.services.description_service.ClaudeClient.complete_vision",
        new_callable=AsyncMock,
        return_value=fake_response,
    ):
        service = DescriptionService(db)
        result = await service.generate(group_id="group-1", custom_prompt=None)

    assert "New York" in result.text
    assert result.tokens_used == 80
```

For Replicate:

```python
with patch(
    "app.integrations.replicate.ReplicateClient.run",
    new_callable=AsyncMock,
    return_value={"output": "https://replicate.delivery/..."},
):
    ...
```

---

## Router Integration Test Pattern

Use the `client` fixture from `conftest.py`. Structure: arrange → act → assert.

```python
def test_health_ready(client: TestClient) -> None:
    # Act
    response = client.get("/api/v1/health/ready")

    # Assert
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_get_session_not_found(client: TestClient) -> None:
    response = client.get("/api/v1/sessions/nonexistent-id")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "SESSION_NOT_FOUND"


def test_create_session(client: TestClient, auth_headers: dict) -> None:
    # Arrange
    payload = {
        "cloud_provider": "google_drive",
        "cloud_folder_id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms",
    }

    # Act
    response = client.post("/api/v1/sessions", json=payload, headers=auth_headers)

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["cloud_provider"] == "google_drive"
    assert data["status"] == "pending"
```

For authenticated routes, add an `auth_headers` fixture that returns a valid JWT header.

---

## Testing File Upload Endpoints

Use `BytesIO` and the `files=` parameter on the TestClient.

```python
import io


def test_upload_corrected_face(client: TestClient, auth_headers: dict) -> None:
    # Arrange — minimal valid JPEG bytes (or load a fixture image)
    with open("api/tests/fixtures/images/face_crop.jpg", "rb") as f:
        image_bytes = f.read()

    # Act
    response = client.post(
        "/api/v1/face-crops/crop-id-123/upload-corrected",
        files={"file": ("face_edited.jpg", io.BytesIO(image_bytes), "image/jpeg")},
        headers=auth_headers,
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["status"] == "uploaded"
```

Fixture images live under `api/tests/fixtures/images/`. Cover JPEG, HEIC, RAW, PNG, and TIFF.

---

## Asserting cost_log Entries

After a paid operation, verify that the cost was recorded correctly.

```python
from sqlalchemy import select
from app.models.cost_log import CostLog


async def test_description_logs_cost(db: AsyncSession) -> None:
    with patch(
        "app.services.description_service.ClaudeClient.complete_vision",
        new_callable=AsyncMock,
        return_value={
            "text": "Caption text",
            "tokens_in": 1000,
            "tokens_out": 100,
            "dollars_cost": 0.018,
        },
    ):
        service = DescriptionService(db)
        await service.generate(group_id="group-1", custom_prompt=None)
        await db.commit()

    # Assert cost_log entry was created
    result = await db.execute(select(CostLog).where(CostLog.session_id == "session-1"))
    entries = result.scalars().all()

    assert len(entries) == 1
    entry = entries[0]
    assert entry.operation == "description"
    assert entry.provider == "claude"
    assert entry.tokens_in == 1000
    assert entry.tokens_out == 100
    assert float(entry.dollars_estimate) == pytest.approx(0.018, rel=1e-4)
```
