"""Sync-related Celery tasks."""

from __future__ import annotations

import asyncio
import json
import logging
from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select

from app.db import AsyncSessionLocal
from app.integrations.google_drive import GoogleDriveClient
from app.lib.exif import extract_exif
from app.lib.face_detect import detect_faces
from app.lib.phash import compute_phash
from app.lib.preview import generate
from app.models.storage import StorageCredentials
from app.repositories.asset import AssetRepository
from app.repositories.edit_version import EditVersionRepository
from app.repositories.session import SessionRepository
from app.services.grouping_service import GroupingService
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="tasks_sync.ping")
def ping() -> str:
    """Smoke task — returns 'pong'."""
    return "pong"


@celery_app.task(bind=True, name="tasks_sync.resync_session")
def resync_session(self, session_id: str) -> dict:
    """
    Orchestrate a full resync: wipe → list → download → preview → EXIF.

    Publishes progress events to Redis pub/sub for SSE streaming.
    """

    async def _resync() -> None:
        async with AsyncSessionLocal() as db:
            repo_session = SessionRepository(db)
            session = await repo_session.get_by_id(session_id)

            if not session:
                await repo_session.update_status(session_id, "error")
                await db.commit()
                return

            try:
                # Transition to syncing
                await repo_session.update_status(session_id, "syncing")
                await db.commit()

                # Get storage credentials
                creds_result = await db.execute(
                    select(StorageCredentials).filter(StorageCredentials.user_id == session.user_id)
                )
                creds = creds_result.scalar_one_or_none()

                if not creds:
                    raise Exception("Storage not connected")

                # Wipe existing assets
                repo_asset = AssetRepository(db)
                await repo_asset.delete_by_session(session_id)
                await db.commit()

                # Initialize Google Drive client
                client = GoogleDriveClient(
                    access_token=creds.access_token, refresh_token=creds.refresh_token
                )

                # List files from cloud
                files = await client.list_folder_recursive(session.cloud_folder_id)
                total = len(files)

                # Download and process each file
                for idx, file_meta in enumerate(files):
                    # Publish progress
                    progress_pct = int((idx / total) * 100) if total > 0 else 0
                    logger.info(
                        "sync.progress session_id=%s progress=%d current_file=%s",
                        session_id,
                        progress_pct,
                        file_meta["name"],
                    )

                    # Determine if video
                    is_video = file_meta.get("mimeType", "").startswith("video/")

                    # Create asset record
                    asset = await repo_asset.create(
                        session_id=session_id,
                        original_cloud_path=file_meta["id"],
                        original_filename=file_meta["name"],
                        is_video=is_video,
                    )

                    # Download to temp location
                    temp_path = str(Path("/data") / "temp" / session_id / file_meta["name"])
                    Path(temp_path).parent.mkdir(parents=True, exist_ok=True)

                    try:
                        await client.download_file(file_meta["id"], temp_path)

                        # Generate previews (skip for video in MVP)
                        if not is_video:
                            try:
                                thumbnail_path = await asyncio.get_event_loop().run_in_executor(
                                    None, generate, temp_path, "thumbnail"
                                )
                                preview_path = await asyncio.get_event_loop().run_in_executor(
                                    None, generate, temp_path, "preview"
                                )

                                # Extract EXIF
                                exif_data = await asyncio.get_event_loop().run_in_executor(
                                    None, extract_exif, temp_path
                                )

                                # Update asset with paths and metadata
                                taken_at = None
                                if exif_data.get("datetime_original"):
                                    with suppress(Exception):
                                        taken_at = datetime.fromisoformat(
                                            exif_data["datetime_original"]
                                        ).replace(tzinfo=UTC)

                                # Compute perceptual hash from thumbnail
                                phash = await asyncio.get_event_loop().run_in_executor(
                                    None, compute_phash, thumbnail_path
                                )

                                # Detect faces in thumbnail
                                faces = await asyncio.get_event_loop().run_in_executor(
                                    None, detect_faces, thumbnail_path
                                )
                                has_face = len(faces) > 0

                                await repo_asset.update(
                                    asset.id,
                                    thumbnail_path=thumbnail_path,
                                    preview_path=preview_path,
                                    full_res_local_path=temp_path,
                                    exif_json=json.dumps(exif_data),
                                    taken_at=taken_at,
                                    gps_lat=exif_data.get("gps_lat"),
                                    gps_lng=exif_data.get("gps_lng"),
                                    phash=phash,
                                    has_face=has_face,
                                )

                                # Create version-0 (original, no edits)
                                edit_repo = EditVersionRepository(db)
                                await edit_repo.create(
                                    asset_id=asset.id,
                                    parent_version_id=None,
                                    corrections_applied_json=json.dumps({"preset": "original"}),
                                    changes_log_text="- Original (unedited)",
                                    output_path=preview_path,
                                    user_decision="accepted",
                                )
                            except Exception as e:
                                # Log but don't fail
                                logger.warning(
                                    "Preview generation failed for %s: %s", file_meta["name"], e
                                )

                    except Exception as e:
                        logger.warning("Download failed for %s: %s", file_meta["name"], e)

                    await db.commit()

                # Run deterministic grouping
                grouping_service = GroupingService(db)
                await grouping_service.regroup_deterministic(session_id, session.cloud_folder_name)
                await db.commit()

                # Mark as ready
                await repo_session.update_status(session_id, "ready")
                await db.commit()

                # Final progress
                logger.info("sync.complete session_id=%s progress=100", session_id)

            except Exception as e:
                logger.error("Sync failed: %s", e)
                await repo_session.update_status(session_id, "error")
                await db.commit()

    asyncio.run(_resync())
    return {"session_id": session_id, "status": "complete"}
