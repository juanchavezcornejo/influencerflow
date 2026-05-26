"""Edit endpoints for color corrections and other modifications."""

from __future__ import annotations

import json
from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.repositories.asset import AssetRepository
from app.repositories.edit_version import EditVersionRepository
from app.routers.storage import get_current_user_id
from app.services.editing_service import EditingService
from app.workers.tasks_editing import apply_corrections_full_res

router = APIRouter(prefix="/edits", tags=["edits"])


class EditProposal(BaseModel):
    """A proposed edit."""

    id: str
    preset_name: str
    preview_url: str
    changes_log_text: str


class SuggestRequest(BaseModel):
    """Request to suggest edits."""

    corrections: list[str]  # ["color", "crop", "remove_objects", "face"]
    mode: str  # "local", "ai"


class AcceptRequest(BaseModel):
    """Request to accept an edit."""

    selected_corrections: list[str]


class RejectRequest(BaseModel):
    """Request to reject an edit."""

    regenerate: bool = False


@router.post("/assets/{asset_id}/suggest")
async def suggest_edits(
    asset_id: str,
    body: SuggestRequest,
    db: AsyncSession = Depends(get_db),
    authorization: str | None = None,
) -> dict[str, list[EditProposal]]:
    """Suggest edits for an asset."""
    get_current_user_id(authorization)

    asset_repo = AssetRepository(db)
    asset = await asset_repo.get_by_id(asset_id)
    if not asset:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND)

    proposals = []

    if "color" in body.corrections:
        if body.mode == "local":
            # Generate local color proposals
            service = EditingService(db)
            color_proposals = await service.propose_colors_local(asset_id)

            edit_repo = EditVersionRepository(db)
            for proposal in color_proposals:
                # Create edit version for each proposal
                changes_log = await service.render_changes_log(proposal.adjustments)
                version = await edit_repo.create(
                    asset_id=asset_id,
                    changes_log_text=changes_log,
                    corrections_applied_json=json.dumps(proposal.adjustments),
                )
                await db.flush()

                proposals.append(
                    EditProposal(
                        id=version.id,
                        preset_name=proposal.preset_name,
                        preview_url=f"/api/v1/edits/{version.id}/preview",
                        changes_log_text=changes_log,
                    )
                )

        elif body.mode == "ai":
            # AI mode not implemented in W3
            raise HTTPException(
                status_code=HTTPStatus.NOT_IMPLEMENTED, detail="AI mode coming in Week 4"
            )

    await db.commit()

    return {"proposals": proposals}


@router.get("/{edit_id}/preview")
async def get_edit_preview(
    edit_id: str,
    db: AsyncSession = Depends(get_db),
    authorization: str | None = None,
) -> dict:
    """Get preview for an edit version."""
    get_current_user_id(authorization)

    edit_repo = EditVersionRepository(db)
    version = await edit_repo.get_by_id(edit_id)

    if not version:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND)

    # For now, return the proposal preview path
    # In production, would stream the file directly
    return {
        "preview_url": version.output_path or "/api/v1/placeholder",
        "changes_log": version.changes_log_text,
    }


@router.post("/{edit_id}/accept")
async def accept_edit(
    edit_id: str,
    body: AcceptRequest,
    db: AsyncSession = Depends(get_db),
    authorization: str | None = None,
) -> dict:
    """Accept an edit and make it current."""
    get_current_user_id(authorization)

    edit_repo = EditVersionRepository(db)
    version = await edit_repo.get_by_id(edit_id)

    if not version:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND)

    # Mark as accepted
    await edit_repo.update(edit_id, user_decision="accepted")
    await db.commit()

    # Trigger full-res apply task
    apply_corrections_full_res.delay(edit_id)

    return {
        "message": "Edit accepted",
        "version_id": edit_id,
        "changes_log": version.changes_log_text,
    }


@router.post("/{edit_id}/reject")
async def reject_edit(
    edit_id: str,
    body: RejectRequest,
    db: AsyncSession = Depends(get_db),
    authorization: str | None = None,
) -> dict:
    """Reject an edit, optionally regenerate."""
    get_current_user_id(authorization)

    edit_repo = EditVersionRepository(db)
    version = await edit_repo.get_by_id(edit_id)

    if not version:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND)

    # Mark as rejected
    await edit_repo.update(edit_id, user_decision="rejected")
    await db.commit()

    if body.regenerate:
        # For W3, just return a message; actual regeneration happens in W4
        return {"message": "Edit rejected. Regeneration coming in Week 4"}

    return {"message": "Edit rejected"}
