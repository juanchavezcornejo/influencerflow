"""Deterministic grouping service: group assets by EXIF date, GPS, time gaps."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.lib.phash import hamming_distance
from app.models.asset import Asset
from app.repositories.asset import AssetRepository
from app.repositories.group import GroupAssetRepository, GroupRepository


class GroupingService:
    """Deterministic grouping logic."""

    # Config
    TIME_GAP_HOURS = 2
    GPS_DISTANCE_METERS = 500
    PHASH_HAMMING_THRESHOLD = 5  # Hamming distance for near-duplicates

    def __init__(self, db: AsyncSession):
        self.db = db
        self.asset_repo = AssetRepository(db)
        self.group_repo = GroupRepository(db)
        self.group_asset_repo = GroupAssetRepository(db)

    def _gps_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Approximate distance in meters using Haversine formula."""
        import math

        R = 6371000  # Earth radius in meters
        lat1_rad, lng1_rad = math.radians(lat1), math.radians(lng1)
        lat2_rad, lng2_rad = math.radians(lat2), math.radians(lng2)

        dlat = lat2_rad - lat1_rad
        dlng = lng2_rad - lng1_rad

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng / 2) ** 2
        )
        c = 2 * math.asin(math.sqrt(a))

        return R * c

    async def regroup_deterministic(self, session_id: str, session_name: str = "") -> None:
        """
        Regroup assets deterministically by EXIF metadata.

        Algorithm:
        1. Sort assets by taken_at (earliest first)
        2. Group by time gap > 2h
        3. Within each time group, split by GPS distance > 500m
        4. Use folder patterns for names if available
        5. Mark auto-generated groups

        Idempotent: wipes prior auto_generated=true groups before re-running.
        """

        # Fetch all assets for this session
        assets = await self.asset_repo.get_by_session(session_id)
        if not assets:
            return

        # Sort by taken_at (earliest first)
        assets_sorted = sorted(assets, key=lambda a: a.taken_at or datetime.now(UTC))

        # Delete prior auto-generated groups
        existing_groups = await self.group_repo.get_by_session(session_id)
        for group in existing_groups:
            if group.auto_generated:
                await self.group_repo.delete(group.id)
        await self.db.commit()

        # Build groups
        current_group_assets = []
        last_time = None
        last_lat, last_lng = None, None
        group_index = 0

        for asset in assets_sorted:
            # Check time gap
            time_gap_exceeded = False
            if last_time and asset.taken_at:
                gap = asset.taken_at - last_time
                if gap > timedelta(hours=self.TIME_GAP_HOURS):
                    time_gap_exceeded = True

            # Check GPS distance
            gps_gap_exceeded = False
            if last_lat is not None and asset.gps_lat is not None and asset.gps_lng is not None:
                distance = self._gps_distance(last_lat, last_lng, asset.gps_lat, asset.gps_lng)
                if distance > self.GPS_DISTANCE_METERS:
                    gps_gap_exceeded = True

            # Start new group if gap detected
            if current_group_assets and (time_gap_exceeded or gps_gap_exceeded):
                await self._save_group(session_id, group_index, current_group_assets)
                current_group_assets = []
                group_index += 1

            # Add asset to current group
            current_group_assets.append(asset)

            # Update last known time/location
            if asset.taken_at:
                last_time = asset.taken_at
            if asset.gps_lat is not None and asset.gps_lng is not None:
                last_lat, last_lng = asset.gps_lat, asset.gps_lng

        # Save final group
        if current_group_assets:
            await self._save_group(session_id, group_index, current_group_assets)

        await self.db.commit()

    def _cluster_near_duplicates(self, assets: list[Asset]) -> dict[str, list[Asset]]:
        """Cluster assets by Hamming distance on phash."""
        clusters = {}
        clustered = set()

        for i, asset in enumerate(assets):
            if i in clustered:
                continue

            cluster = [asset]
            clustered.add(i)

            # Find all assets similar to this one
            if asset.phash:
                for j, other in enumerate(assets[i + 1 :], start=i + 1):
                    if j in clustered or not other.phash:
                        continue

                    distance = hamming_distance(asset.phash, other.phash)
                    if distance < self.PHASH_HAMMING_THRESHOLD:
                        cluster.append(other)
                        clustered.add(j)

            # Select representative with highest aesthetic score (fallback: first in cluster)
            representative = max(
                cluster,
                key=lambda a: (
                    a.aesthetic_score or 0,
                    assets.index(a) * -1,
                ),  # Sort by score desc, then by time asc
            )
            cluster_id = representative.id
            clusters[cluster_id] = cluster

        return clusters

    async def _save_group(self, session_id: str, index: int, assets: list[Asset]) -> None:
        """Helper: save a group with its assets."""
        # Generate name from first asset's date or location
        group_name = f"Group {index + 1}"
        if assets and assets[0].taken_at:
            group_name = assets[0].taken_at.strftime("%Y-%m-%d")

        # Create group
        group = await self.group_repo.create(session_id, group_name, auto_generated=True)

        # Cluster near-duplicates
        clusters = self._cluster_near_duplicates(assets)

        # Add assets with cluster assignments
        for position, asset in enumerate(assets):
            # Find which cluster this asset belongs to
            cluster_id = None
            for cid, cluster_assets in clusters.items():
                if asset in cluster_assets:
                    cluster_id = cid
                    break

            # Update asset's near_duplicate_cluster_id
            if cluster_id:
                await self.asset_repo.update(asset.id, near_duplicate_cluster_id=cluster_id)

            # Add to group
            await self.group_asset_repo.add_asset(group.id, asset.id, position)
