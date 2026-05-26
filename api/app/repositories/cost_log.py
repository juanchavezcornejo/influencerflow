"""Cost log repository."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cost_log import CostLog


class CostLogRepository:
    """Data access for CostLog model."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        session_id: str,
        operation: str,
        model: str | None = None,
        tokens_in: int | None = None,
        tokens_out: int | None = None,
        dollars_estimate: float | None = None,
    ) -> CostLog:
        """Create a cost log entry."""
        entry = CostLog(
            session_id=session_id,
            operation=operation,
            model=model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            dollars_estimate=dollars_estimate,
        )
        self.db.add(entry)
        await self.db.flush()
        return entry

    async def get_session_total(self, session_id: str) -> dict:
        """Get total costs for a session."""
        result = await self.db.execute(
            select(
                func.sum(CostLog.dollars_estimate).label("total_dollars"),
                CostLog.operation,
                func.count(CostLog.id).label("count"),
            )
            .filter(CostLog.session_id == session_id)
            .group_by(CostLog.operation)
        )

        total_dollars = 0.0
        by_operation = []

        for row in result:
            total = row[0] or 0.0
            operation = row[1]
            count = row[2]
            total_dollars += total
            by_operation.append(
                {
                    "operation": operation,
                    "count": count,
                    "dollars": total,
                }
            )

        return {
            "total_dollars": total_dollars,
            "by_operation": by_operation,
        }
