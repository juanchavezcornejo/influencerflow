"""Endpoints for description generation and management."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import RuntimeSettings
from app.db import get_db
from app.dependencies import get_current_user, get_runtime_settings
from app.models.user import User
from app.repositories.description import DescriptionRepository
from app.services.description_service import DescriptionService

router = APIRouter(prefix="/api/v1", tags=["descriptions"])


class DescriptionRequest(BaseModel):
    custom_prompt: str | None = None


class DescriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    group_id: str
    text: str
    is_current: bool
    tokens_in: int | None
    tokens_out: int | None
    created_at: str


class DescriptionsListResponse(BaseModel):
    descriptions: list[DescriptionResponse]


@router.post("/groups/{group_id}/descriptions/generate")
async def generate_description(
    group_id: str,
    req: DescriptionRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    runtime: RuntimeSettings = Depends(get_runtime_settings),
) -> DescriptionResponse:
    """
    Generate a description for a group.

    POST /api/v1/groups/{group_id}/descriptions/generate
    {
      "custom_prompt": "optional guidance for Claude"
    }
    """
    try:
        service = DescriptionService(session, anthropic_api_key=runtime.anthropic_api_key)
        desc = await service.generate(
            group_id=group_id,
            custom_prompt=req.custom_prompt,
        )

        return DescriptionResponse(
            id=desc.id,
            group_id=desc.group_id,
            text=desc.text,
            is_current=desc.is_current,
            tokens_in=desc.tokens_in,
            tokens_out=desc.tokens_out,
            created_at=desc.created_at.isoformat(),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/groups/{group_id}/descriptions")
async def list_descriptions(
    group_id: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> DescriptionsListResponse:
    """
    List descriptions for a group, newest first.

    GET /api/v1/groups/{group_id}/descriptions
    """
    try:
        repo = DescriptionRepository(session)
        descriptions = await repo.get_by_group(group_id)

        return DescriptionsListResponse(
            descriptions=[
                DescriptionResponse(
                    id=d.id,
                    group_id=d.group_id,
                    text=d.text,
                    is_current=d.is_current,
                    tokens_in=d.tokens_in,
                    tokens_out=d.tokens_out,
                    created_at=d.created_at.isoformat(),
                )
                for d in descriptions
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/descriptions/{description_id}/set-current")
async def set_current_description(
    description_id: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> DescriptionResponse:
    """
    Set a description as the current one for its group.

    POST /api/v1/descriptions/{description_id}/set-current
    """
    try:
        repo = DescriptionRepository(session)
        desc = await repo.get_by_id(description_id)
        if not desc:
            raise HTTPException(status_code=404, detail="Description not found")

        updated = await repo.set_current(desc.group_id, description_id)
        await session.commit()

        return DescriptionResponse(
            id=updated.id,
            group_id=updated.group_id,
            text=updated.text,
            is_current=updated.is_current,
            tokens_in=updated.tokens_in,
            tokens_out=updated.tokens_out,
            created_at=updated.created_at.isoformat(),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
