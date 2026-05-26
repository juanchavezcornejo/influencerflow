"""Server-Sent Events endpoints for real-time progress."""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.repositories.session import SessionRepository
from app.routers.storage import get_current_user_id

router = APIRouter(prefix="/events", tags=["events"])


async def event_stream(session_id: str, db: AsyncSession) -> None:
    """Stream events for a session (generator for SSE)."""
    repo = SessionRepository(db)
    session = await repo.get_by_id(session_id)

    if not session:
        yield f"data: {json.dumps({'type': 'error', 'message': 'Session not found'})}\n\n"
        return

    # Simple implementation: poll session status and emit events
    # In production, would use Redis pub/sub for better scalability
    last_status = session.status
    counter = 0

    while counter < 300:  # Max 5 minutes of streaming
        await asyncio.sleep(1)
        counter += 1

        # Re-fetch session to check status
        updated = await repo.get_by_id(session_id)
        if updated and updated.status != last_status:
            event = {
                "type": "sync.status_changed",
                "status": updated.status,
            }
            yield f"data: {json.dumps(event)}\n\n"
            last_status = updated.status

            # Close stream when sync completes or errors
            if updated.status in ("ready", "error"):
                break


@router.get("/session/{session_id}")
async def stream_session_events(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    authorization: str | None = Header(None),
) -> StreamingResponse:
    """Stream real-time events for a session via Server-Sent Events."""
    user_id = get_current_user_id(authorization)

    # Verify user owns this session
    repo = SessionRepository(db)
    session = await repo.get_by_id(session_id)

    if not session or session.user_id != user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    return StreamingResponse(
        event_stream(session_id, db),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
