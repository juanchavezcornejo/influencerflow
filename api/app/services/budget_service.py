"""Budget guard service for session cost management."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.cost_log import CostLog


class BudgetService:
    """Manage session budgets and cost limits."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_session_spending(self, session_id: str) -> float:
        """Get total spending for a session so far."""
        result = await self.session.execute(
            select(func.sum(CostLog.dollars_estimate)).where(CostLog.session_id == session_id)
        )
        total = result.scalar() or 0.0
        return float(total)

    async def check_budget(self, session_id: str, operation_cost: float) -> dict:
        """
        Check if an operation would exceed budget limits.

        Returns:
        {
            "allowed": bool,
            "exceeded_soft": bool,
            "exceeded_hard": bool,
            "current_spending": float,
            "soft_limit": float,
            "hard_limit": float,
            "remaining": float,
        }
        """
        soft_limit = float(settings.session_budget_usd)
        hard_limit = float(settings.session_hard_cap_usd)

        current = await self.get_session_spending(session_id)
        new_total = current + operation_cost
        remaining = soft_limit - current

        exceeded_soft = new_total > soft_limit
        exceeded_hard = new_total > hard_limit

        return {
            "allowed": not exceeded_hard,
            "exceeded_soft": exceeded_soft,
            "exceeded_hard": exceeded_hard,
            "current_spending": current,
            "soft_limit": soft_limit,
            "hard_limit": hard_limit,
            "remaining": max(0, remaining),
            "new_total": new_total,
        }
