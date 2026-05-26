"""Liveness + readiness endpoints."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: Literal["ok"]


class ReadyResponse(BaseModel):
    status: Literal["ready", "not_ready"]
    db: Literal["ok", "error"]


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Liveness: the process is up."""
    return HealthResponse(status="ok")


@router.get("/health/ready", response_model=ReadyResponse)
async def ready(
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> ReadyResponse:
    """Readiness: the DB is reachable."""
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return ReadyResponse(status="not_ready", db="error")
    return ReadyResponse(status="ready", db="ok")
