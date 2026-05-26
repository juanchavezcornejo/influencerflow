"""Tests for grouping_service.py"""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db import Base
from app.models.asset import Asset
from app.models.session import Session
from app.repositories.group import GroupRepository
from app.services.grouping_service import GroupingService


@pytest.fixture
async def db():
    """Create in-memory test database."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_grouping_same_day_single_location(db: AsyncSession):
    """Test grouping assets from same day at same location."""
    # Create session
    session = Session(
        id="test-session", user_id="user1", cloud_folder_id="folder1", cloud_folder_name="Test"
    )
    db.add(session)
    await db.flush()

    # Create assets from same day, same location
    base_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC)
    for i in range(3):
        asset = Asset(
            session_id="test-session",
            original_cloud_path=f"file{i}",
            original_filename=f"file{i}.jpg",
            taken_at=base_time + timedelta(hours=i),
            gps_lat=40.7128,
            gps_lng=-74.0060,
        )
        db.add(asset)
    await db.commit()

    # Run grouping
    service = GroupingService(db)
    await service.regroup_deterministic("test-session", "Test")
    await db.commit()

    # Verify single group was created
    repo = GroupRepository(db)
    groups = await repo.get_by_session("test-session")
    assert len(groups) == 1
    assert groups[0].auto_generated is True


@pytest.mark.asyncio
async def test_grouping_time_gap(db: AsyncSession):
    """Test grouping splits on 2+ hour time gap."""
    session = Session(
        id="test-session", user_id="user1", cloud_folder_id="folder1", cloud_folder_name="Test"
    )
    db.add(session)
    await db.flush()

    # Create assets with 3-hour gap
    base_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC)
    times = [base_time, base_time + timedelta(hours=1), base_time + timedelta(hours=4)]

    for i, time in enumerate(times):
        asset = Asset(
            session_id="test-session",
            original_cloud_path=f"file{i}",
            original_filename=f"file{i}.jpg",
            taken_at=time,
            gps_lat=40.7128,
            gps_lng=-74.0060,
        )
        db.add(asset)
    await db.commit()

    # Run grouping
    service = GroupingService(db)
    await service.regroup_deterministic("test-session", "Test")
    await db.commit()

    # Verify two groups (split at 2-hour gap)
    repo = GroupRepository(db)
    groups = await repo.get_by_session("test-session")
    assert len(groups) == 2


@pytest.mark.asyncio
async def test_grouping_gps_distance(db: AsyncSession):
    """Test grouping splits on GPS distance > 500m."""
    session = Session(
        id="test-session", user_id="user1", cloud_folder_id="folder1", cloud_folder_name="Test"
    )
    db.add(session)
    await db.flush()

    base_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC)

    # NYC location
    asset1 = Asset(
        session_id="test-session",
        original_cloud_path="file1",
        original_filename="file1.jpg",
        taken_at=base_time,
        gps_lat=40.7128,
        gps_lng=-74.0060,
    )
    db.add(asset1)

    # San Francisco (2600 km away)
    asset2 = Asset(
        session_id="test-session",
        original_cloud_path="file2",
        original_filename="file2.jpg",
        taken_at=base_time + timedelta(hours=1),
        gps_lat=37.7749,
        gps_lng=-122.4194,
    )
    db.add(asset2)
    await db.commit()

    # Run grouping
    service = GroupingService(db)
    await service.regroup_deterministic("test-session", "Test")
    await db.commit()

    # Verify two groups
    repo = GroupRepository(db)
    groups = await repo.get_by_session("test-session")
    assert len(groups) == 2


@pytest.mark.asyncio
async def test_grouping_idempotent(db: AsyncSession):
    """Test grouping is idempotent."""
    session = Session(
        id="test-session", user_id="user1", cloud_folder_id="folder1", cloud_folder_name="Test"
    )
    db.add(session)
    await db.flush()

    # Create assets
    for i in range(3):
        asset = Asset(
            session_id="test-session",
            original_cloud_path=f"file{i}",
            original_filename=f"file{i}.jpg",
            taken_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC),
            gps_lat=40.7128,
            gps_lng=-74.0060,
        )
        db.add(asset)
    await db.commit()

    # Run grouping twice
    service = GroupingService(db)
    await service.regroup_deterministic("test-session", "Test")
    await db.commit()

    repo = GroupRepository(db)
    groups1 = await repo.get_by_session("test-session")

    await service.regroup_deterministic("test-session", "Test")
    await db.commit()

    groups2 = await repo.get_by_session("test-session")

    # Same number of groups
    assert len(groups1) == len(groups2)
