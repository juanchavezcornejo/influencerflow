"""Cost estimation endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.routers.storage import get_current_user_id
from app.services.cost_service import CostEstimator

router = APIRouter(prefix="/cost", tags=["cost"])


class CostEstimateRequest(BaseModel):
    """Request for cost estimate."""

    operation: str  # "object_removal", "color_ai", "description", etc
    inputs: dict | None = None


class CostEstimateResponse(BaseModel):
    """Cost estimate response."""

    tokens_in: int
    tokens_out: int
    dollars: float
    model: str


@router.post("/estimate")
async def estimate_cost(
    body: CostEstimateRequest,
    db: AsyncSession = Depends(get_db),
    authorization: str | None = None,
) -> CostEstimateResponse:
    """Estimate cost for an operation."""
    get_current_user_id(authorization)

    estimate = CostEstimator.estimate(body.operation, body.inputs or {})

    return CostEstimateResponse(
        tokens_in=estimate.get("tokens_in", 0),
        tokens_out=estimate.get("tokens_out", 0),
        dollars=estimate.get("dollars", 0.0),
        model=estimate.get("model", "unknown"),
    )
