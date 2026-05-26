"""Session management endpoints."""

from __future__ import annotations

from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.cost_log import CostLog
from app.repositories.session import SessionRepository
from app.routers.storage import get_current_user_id

router = APIRouter(prefix="/sessions", tags=["sessions"])


class CreateSessionRequest(BaseModel):
    """Create session request."""

    cloud_provider: str
    cloud_folder_id: str
    cloud_folder_name: str


class SessionResponse(BaseModel):
    """Session response."""

    id: str
    cloud_provider: str
    cloud_folder_id: str
    cloud_folder_name: str
    status: str
    created_at: str


class CostLogEntry(BaseModel):
    """Single cost log entry."""

    operation: str
    count: int
    dollars: float


class SessionCostResponse(BaseModel):
    """Session cost breakdown."""

    total_dollars: float
    by_operation: list[CostLogEntry]


@router.post("", response_model=SessionResponse)
async def create_session(
    req: CreateSessionRequest,
    db: AsyncSession = Depends(get_db),
    authorization: str | None = None,
) -> SessionResponse:
    """Create a new session from a cloud folder."""
    user_id = get_current_user_id(authorization)
    repo = SessionRepository(db)
    session = await repo.create(
        user_id=user_id,
        cloud_provider=req.cloud_provider,
        cloud_folder_id=req.cloud_folder_id,
        cloud_folder_name=req.cloud_folder_name,
    )
    await db.commit()
    return SessionResponse(
        id=session.id,
        cloud_provider=session.cloud_provider,
        cloud_folder_id=session.cloud_folder_id,
        cloud_folder_name=session.cloud_folder_name,
        status=session.status,
        created_at=session.created_at.isoformat(),
    )


@router.get("", response_model=list[SessionResponse])
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    authorization: str | None = None,
) -> list[SessionResponse]:
    """List all sessions for current user."""
    user_id = get_current_user_id(authorization)
    repo = SessionRepository(db)
    sessions = await repo.get_by_user(user_id)
    return [
        SessionResponse(
            id=s.id,
            cloud_provider=s.cloud_provider,
            cloud_folder_id=s.cloud_folder_id,
            cloud_folder_name=s.cloud_folder_name,
            status=s.status,
            created_at=s.created_at.isoformat(),
        )
        for s in sessions
    ]


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    authorization: str | None = None,
) -> SessionResponse:
    """Get session details."""
    user_id = get_current_user_id(authorization)
    repo = SessionRepository(db)
    session = await repo.get_by_id(session_id)

    if not session or session.user_id != user_id:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Session not found")

    return SessionResponse(
        id=session.id,
        cloud_provider=session.cloud_provider,
        cloud_folder_id=session.cloud_folder_id,
        cloud_folder_name=session.cloud_folder_name,
        status=session.status,
        created_at=session.created_at.isoformat(),
    )


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    authorization: str | None = None,
) -> dict:
    """Delete a session (soft delete)."""
    user_id = get_current_user_id(authorization)
    repo = SessionRepository(db)
    session = await repo.get_by_id(session_id)

    if not session or session.user_id != user_id:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Session not found")

    await repo.mark_deleted(session_id)
    await db.commit()
    # TODO: Schedule cleanup task for temp files
    return {"message": "Session deleted"}


@router.get("/{session_id}/cost", response_model=SessionCostResponse)
async def get_session_cost(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    authorization: str | None = None,
) -> SessionCostResponse:
    """Get cost breakdown for a session."""
    user_id = get_current_user_id(authorization)
    repo = SessionRepository(db)
    session = await repo.get_by_id(session_id)

    if not session or session.user_id != user_id:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Session not found")

    # Calculate total and per-operation costs
    result = await db.execute(
        select(
            CostLog.operation,
            func.count(CostLog.id).label("count"),
            func.sum(CostLog.dollars_estimate).label("total_dollars"),
        )
        .where(CostLog.session_id == session_id)
        .group_by(CostLog.operation)
    )
    rows = result.all()

    total = 0.0
    by_operation = []
    for row in rows:
        op_total = row.total_dollars or 0.0
        total += op_total
        by_operation.append(
            CostLogEntry(
                operation=row.operation,
                count=row.count,
                dollars=op_total,
            )
        )

    return SessionCostResponse(total_dollars=total, by_operation=by_operation)
