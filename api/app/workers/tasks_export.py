"""Export tasks — ZIP building and management."""

import json
import logging
import shutil
from pathlib import Path

from sqlalchemy import select

from app.config import settings
from app.db import AsyncSessionLocal
from app.models.asset import Asset
from app.models.edit_version import EditVersion
from app.models.group import Group
from app.models.session import Session
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="tasks_export.build_zip")
def build_zip(self, group_id: str):
    """
    Build a ZIP file for a group with all final-res edits.

    Steps:
    1. Load group + assets (in position order)
    2. For each asset, find current edit_version.output_path (or original)
    3. Copy to temp dir with naming: {NN}_{place_or_date}.{ext}
    4. ZIP into /data/exports/{session_id}/{group_id}.zip
    5. Emit export.ready SSE event
    """
    import asyncio

    # Run async code in this sync task context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_build_zip_async(group_id, self))
    finally:
        loop.close()


async def _build_zip_async(group_id: str, task):
    """Async implementation of ZIP building."""
    session = AsyncSessionLocal()

    try:
        # Load group
        result = await session.execute(select(Group).where(Group.id == group_id))
        group = result.scalar_one_or_none()
        if not group:
            raise ValueError(f"Group {group_id} not found")

        # Load session
        result = await session.execute(select(Session).where(Session.id == group.session_id))
        sess = result.scalar_one_or_none()
        if not sess:
            raise ValueError(f"Session {group.session_id} not found")

        # Load assets in group (ordered by position)
        result = await session.execute(
            select(Asset)
            .join(Asset.group_assets)
            .where(Asset.group_assets.any(group_id=group_id))
            .order_by(Asset.group_assets.c.position)
        )
        assets = result.scalars().all()

        # Create temp dir
        temp_dir = settings.data_dir / "temp_exports" / group_id
        temp_dir.mkdir(parents=True, exist_ok=True)

        # Copy/rename files
        for pos, asset in enumerate(assets, 1):
            # Determine source path (edit output or original)
            source_path = None

            # Check for current edit version
            result = await session.execute(
                select(EditVersion)
                .where(EditVersion.asset_id == asset.id, EditVersion.user_decision == "accepted")
                .order_by(EditVersion.created_at.desc())
            )
            current_edit = result.scalar_one_or_none()

            if current_edit and current_edit.output_path:
                source_path = current_edit.output_path
            elif asset.full_res_local_path:
                source_path = asset.full_res_local_path
            else:
                # Skip if no source
                continue

            # Determine destination filename
            place = ""
            _exif: dict = {}
            if asset.exif_json:
                try:
                    _exif = json.loads(asset.exif_json)
                except (ValueError, TypeError):
                    _exif = {}
            if _exif.get("location"):
                place = _exif["location"][:20].replace(" ", "_").lower()
            elif asset.taken_at:
                place = asset.taken_at.strftime("%Y%m%d").lower()
            else:
                place = "unknown"

            ext = Path(source_path).suffix
            dest_filename = f"{pos:02d}_{place}{ext}"
            dest_path = temp_dir / dest_filename

            # Copy file
            if Path(source_path).exists():
                shutil.copy2(source_path, dest_path)

        # Create ZIP
        export_dir = settings.data_dir / "exports" / sess.id
        export_dir.mkdir(parents=True, exist_ok=True)
        zip_path = export_dir / f"{group_id}.zip"

        shutil.make_archive(str(zip_path.with_suffix("")), "zip", temp_dir)

        # Clean up temp
        shutil.rmtree(temp_dir)

        logger.info(
            "export.ready session_id=%s group_id=%s zip_path=%s",
            sess.id,
            group_id,
            zip_path,
        )

        return {"group_id": group_id, "zip_path": str(zip_path), "status": "ready"}

    finally:
        await session.close()
