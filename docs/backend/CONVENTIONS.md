# Backend Conventions

FastAPI + SQLAlchemy async conventions for InfluencerFlow.

---

## Layer Architecture

The backend is strictly layered. Each layer has a single responsibility and may only call the layer below it.

```
Router  →  Service  →  Repository  →  ORM Model
```

**Hard rules per layer:**

| Layer | Lives in | Rules |
|---|---|---|
| Router | `app/routers/` | Validates request shape, calls service or repo, raises `HTTPException`, returns Pydantic schema. No raw SQL. No business logic. |
| Service | `app/services/` | Business logic only. Calls repositories. Raises `ValueError` (not `HTTPException`). Does not touch HTTP. |
| Repository | `app/repositories/` | One class per model. Raw SQLAlchemy queries only. Calls `db.flush()` (never `db.commit()`). Commit belongs to the caller (router or service). |
| Model | `app/models/` | SQLAlchemy ORM class only. No methods. No business logic. |

---

## File Naming

| Layer | Pattern | Example |
|---|---|---|
| Router | `app/routers/<resource>.py` | `app/routers/sessions.py` |
| Service | `app/services/<resource>_service.py` | `app/services/grouping_service.py` |
| Repository | `app/repositories/<resource>.py` | `app/repositories/session.py` |
| ORM Model | `app/models/<resource>.py` | `app/models/session.py` |
| Pydantic Schema | `app/schemas/<resource>.py` | `app/schemas/auth.py` |

---

## Router Pattern

```python
"""Widget management endpoints."""

from __future__ import annotations

from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.repositories.widget import WidgetRepository

router = APIRouter(prefix="/widgets", tags=["widgets"])


class WidgetResponse(BaseModel):
    id: str
    name: str
    sessionId: str  # camelCase for JSON responses

    model_config = ConfigDict(from_attributes=True)


@router.get("/{widget_id}", response_model=WidgetResponse)
async def get_widget(
    widget_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WidgetResponse:
    repo = WidgetRepository(db)
    widget = await repo.get_by_id(widget_id)

    if not widget or widget.user_id != current_user.id:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Widget not found")

    return WidgetResponse(id=widget.id, name=widget.name, sessionId=widget.session_id)
```

Key points:
- Always import `HTTPStatus` from `http`, never hardcode integers.
- Ownership check: compare `resource.user_id` to `current_user.id` before returning.
- `response_model=` declared on every route.
- `await db.commit()` is called in the router after mutating operations, not inside the repo.

---

## Service Pattern

```python
"""Widget grouping logic."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.widget import WidgetRepository
from app.repositories.group import GroupRepository


class WidgetService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.widget_repo = WidgetRepository(db)
        self.group_repo = GroupRepository(db)

    async def regroup(self, session_id: str) -> None:
        widgets = await self.widget_repo.get_by_session(session_id)
        if not widgets:
            return

        # ... business logic ...

        # Raise ValueError for domain errors — never HTTPException
        if some_invalid_condition:
            raise ValueError("Cannot regroup: reason")

        await self.db.commit()  # services may commit when they own the transaction
```

---

## Repository Pattern

```python
"""Widget repository."""

from __future__ import annotations

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.widget import Widget


class WidgetRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, widget_id: str) -> Widget | None:
        result = await self.db.execute(select(Widget).filter(Widget.id == widget_id))
        return result.scalar_one_or_none()

    async def create(self, session_id: str, name: str) -> Widget:
        widget = Widget(session_id=session_id, name=name)
        self.db.add(widget)
        await self.db.flush()   # flush writes to transaction; caller commits
        return widget

    async def update_name(self, widget_id: str, name: str) -> Widget | None:
        widget = await self.get_by_id(widget_id)
        if widget:
            widget.name = name
            await self.db.flush()  # flush, not commit
        return widget
```

**flush vs commit rule:** repositories always call `db.flush()`. This writes the change to the current transaction without releasing it. The router (or service that owns the outer transaction) calls `await db.commit()`.

---

## ORM Model Pattern

```python
"""Widget model."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Widget(Base):
    __tablename__ = "widgets"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: __import__("uuid").uuid4().hex
    )
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("sessions.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
```

Rules:
- Primary key is a UUID stored as `String(36)`, defaulted with `uuid4().hex`.
- All `DateTime` columns are timezone-aware (`DateTime(timezone=True)`).
- Default and `onupdate` use lambda to defer evaluation.
- No methods, no business logic on the model class.

---

## Pydantic Schema Pattern

```python
from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class WidgetResponse(BaseModel):
    """Response schema — camelCase field names for JSON output."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    sessionId: str          # camelCase, not session_id
    name: str
    createdAt: str          # ISO 8601 string


class CreateWidgetRequest(BaseModel):
    """Request body — snake_case is fine (JSON parsers handle both)."""

    session_id: str
    name: str
```

Rules:
- All response schemas use `ConfigDict(from_attributes=True)` to allow construction from ORM objects.
- JSON response field names use **camelCase** to match the frontend convention.
- Request schemas use snake_case (FastAPI / Pydantic coerce automatically).
- Never return raw ORM objects from routers — always convert to a Pydantic schema.

---

## Error Handling

| Layer | Mechanism | Example |
|---|---|---|
| Router | `raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="...")` | Resource not found or ownership mismatch |
| Router | `raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, ...)` | Missing or invalid token |
| Router | `raise HTTPException(status_code=HTTPStatus.UNPROCESSABLE_ENTITY, ...)` | Validation that Pydantic misses |
| Service | `raise ValueError("reason")` | Business rule violation |
| Router catches service | `except ValueError as e: raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(e))` | Convert service errors to HTTP |

Standard codes used:
- `200 OK` — success
- `201 Created` — not currently used (POST returns 200 in this project)
- `400 Bad Request` — bad input after validation
- `401 Unauthorized` — auth missing or invalid
- `403 Forbidden` — authenticated but not allowed
- `404 Not Found` — resource does not exist or ownership mismatch
- `422 Unprocessable Entity` — FastAPI default for Pydantic validation errors
- `500 Internal Server Error` — unhandled exceptions

---

## Logging

```python
import logging

logger = logging.getLogger(__name__)

# Usage — always include structured extra fields:
logger.info(
    "sync.progress session_id=%s progress=%d current_file=%s",
    session_id, progress_pct, file_name,
)
logger.warning("preview.failed asset_id=%s reason=%s", asset_id, str(e))
logger.error("task.failed task=%s error=%s", task_name, str(e))
```

Rules:
- Use `logging.getLogger(__name__)` — one logger per module, no global logger.
- Always include relevant IDs (`session_id`, `asset_id`, `group_id`) in log messages.
- Use `%s`-style formatting (not f-strings) to defer interpolation.
- Log at `INFO` for normal progress, `WARNING` for recoverable errors, `ERROR` for task failures.

---

## Config Access

Always import the singleton:

```python
from app.config import settings

# Correct
db_url = settings.database_url
budget = settings.session_budget_usd

# Never
import os
db_url = os.environ["DATABASE_URL"]  # forbidden
```

`settings` is a cached `pydantic_settings.BaseSettings` instance. All env vars are validated at startup. Access via `settings.*` only.

---

## Adding an Endpoint Checklist

1. Create or open `app/routers/<resource>.py`. Add the route function with `response_model=`.
2. Define request body and response schemas in `app/schemas/<resource>.py` (or inline in the router for simple cases).
3. Add business logic to `app/services/<resource>_service.py` if the logic is non-trivial.
4. Add data access to `app/repositories/<resource>.py`. Use `flush()`, not `commit()`.
5. Add ownership check: verify `resource.user_id == current_user.id` before returning or mutating.
6. Call `await db.commit()` in the router after all mutations.
7. Register the router in `app/main.py` under `API_V1_PREFIX` (or without prefix for non-v1 routes).

---

## Code Style

- **Python version:** 3.12
- **First line of every module:** `from __future__ import annotations`
- **Line length:** 100 characters (enforced by ruff)
- **Import order** (ruff/isort):
  1. `from __future__ import annotations`
  2. Standard library
  3. Third-party (`fastapi`, `sqlalchemy`, `pydantic`, …)
  4. Internal (`app.*`)
- **Type hints:** always on function signatures; use `X | None` (not `Optional[X]`).
- **Formatter:** ruff format (via `make format`)
- **Linter:** ruff + mypy (via `make lint`)
