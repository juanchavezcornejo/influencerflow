"""Face crop endpoints for face retouch workflow."""

from __future__ import annotations

import json
import logging
from http import HTTPStatus
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.lib.face_detect import detect_faces
from app.repositories.asset import AssetRepository
from app.repositories.face_crop import FaceCropRepository
from app.routers.storage import get_current_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/face-crops", tags=["face_crops"])


class FaceCropResponse(BaseModel):
    """Face crop response."""

    id: str
    bbox: dict
    status: str


@router.post("/assets/{asset_id}")
async def create_face_crops(
    asset_id: str,
    db: AsyncSession = Depends(get_db),
    authorization: str | None = None,
) -> list[FaceCropResponse]:
    """Create face crops from asset's full-res image."""
    get_current_user_id(authorization)

    asset_repo = AssetRepository(db)
    asset = await asset_repo.get_by_id(asset_id)

    if not asset or not asset.full_res_local_path:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND)

    try:
        # Detect faces
        faces = detect_faces(asset.full_res_local_path)

        if not faces:
            return []

        face_crop_repo = FaceCropRepository(db)
        results = []

        # Create crop for each detected face
        crop_dir = Path("/data/face_crops") / asset_id
        crop_dir.mkdir(parents=True, exist_ok=True)

        for i, face_bbox in enumerate(faces):
            # Save crop
            crop_path = crop_dir / f"face_{i}.png"

            bbox_json = json.dumps(face_bbox)

            crop = await face_crop_repo.create(
                asset_id=asset_id,
                bbox_json=bbox_json,
                crop_path=str(crop_path),
            )

            results.append(FaceCropResponse(id=crop.id, bbox=face_bbox, status="cropped"))

        await db.commit()
        return results

    except Exception as e:
        logger.error("Face crop creation failed: %s", e)
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR) from e


@router.get("/{crop_id}/download")
async def download_face_crop(
    crop_id: str,
    db: AsyncSession = Depends(get_db),
    authorization: str | None = None,
) -> FileResponse:
    """Download a face crop PNG."""
    get_current_user_id(authorization)

    face_crop_repo = FaceCropRepository(db)
    crop = await face_crop_repo.get_by_id(crop_id)

    if not crop or not crop.crop_path:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND)

    path = Path(crop.crop_path)
    if not path.exists():
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Crop file not found")

    return FileResponse(
        path,
        media_type="image/png",
        filename=f"face_crop_{crop_id}.png",
    )


class UploadCorrectedRequest(BaseModel):
    """Upload corrected face crop."""

    pass


@router.post("/{crop_id}/upload-corrected")
async def upload_corrected_face(
    crop_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    authorization: str | None = None,
) -> dict:
    """Upload corrected face crop (e.g., from FaceApp)."""
    get_current_user_id(authorization)

    face_crop_repo = FaceCropRepository(db)
    crop = await face_crop_repo.get_by_id(crop_id)

    if not crop:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND)

    try:
        # Validate file type
        if file.content_type not in ["image/png", "image/jpeg"]:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Only PNG/JPEG allowed")

        # Save file
        upload_dir = Path("/data/face_crops") / crop.asset_id / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        upload_path = upload_dir / f"corrected_{crop_id}.png"

        contents = await file.read()
        with open(upload_path, "wb") as f:
            f.write(contents)

        # Update crop
        await face_crop_repo.update(crop_id, user_uploaded_path=str(upload_path), status="uploaded")
        await db.commit()

        return {"message": "Upload successful", "status": "uploaded"}

    except Exception as e:
        logger.error("Upload failed: %s", e)
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR) from e
