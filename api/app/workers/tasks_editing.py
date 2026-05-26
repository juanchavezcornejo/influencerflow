"""Editing-related Celery tasks."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from PIL import Image

from app.db import AsyncSessionLocal
from app.lib.color_ops import apply_corrections
from app.repositories.asset import AssetRepository
from app.repositories.edit_version import EditVersionRepository
from app.workers.celery_app import celery_app


@celery_app.task(name="tasks_editing.apply_corrections")
def apply_corrections_full_res(edit_version_id: str) -> dict:
    """Apply color corrections to full-resolution image and save output."""

    async def _apply() -> None:
        async with AsyncSessionLocal() as db:
            edit_repo = EditVersionRepository(db)
            version = await edit_repo.get_by_id(edit_version_id)

            if not version:
                return

            asset_repo = AssetRepository(db)
            asset = await asset_repo.get_by_id(version.asset_id)

            if not asset or not asset.full_res_local_path:
                return

            try:
                # Load corrections
                if not version.corrections_applied_json:
                    return

                corrections = json.loads(version.corrections_applied_json)

                # Load full-res image
                full_res = Image.open(asset.full_res_local_path).convert("RGB")

                # Apply corrections
                corrected = apply_corrections(full_res, corrections)

                # Save output
                output_dir = Path("/data/edits") / asset.id
                output_dir.mkdir(parents=True, exist_ok=True)
                output_path = output_dir / f"{version.id}.jpg"
                corrected.save(str(output_path), "JPEG", quality=95)

                # Update version with output path
                await edit_repo.update(edit_version_id, output_path=str(output_path))
                await db.commit()

            except Exception as e:
                print(f"Failed to apply corrections: {e}")
                await edit_repo.update(edit_version_id, output_path=None)
                await db.commit()

    asyncio.run(_apply())
    return {"edit_version_id": edit_version_id, "status": "completed"}
