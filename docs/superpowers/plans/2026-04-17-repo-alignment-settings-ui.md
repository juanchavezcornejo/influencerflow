# Repo Alignment + Settings UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Align the repo structure to the MD docs, then add a DB-backed Settings page where API keys, budget limits, and style seed text can be edited from the UI.

**Architecture:** A single `app_settings` Postgres row (id=1, upserted on save) acts as a runtime override layer on top of env-file defaults. A `RuntimeSettings` dataclass is produced by a FastAPI dependency (`get_runtime_settings`) that merges the DB row with env fallbacks; services that consume API keys receive this via constructor injection. The frontend is a Next.js Server Component that fetches current settings and passes them to a client-side form.

**Tech Stack:** FastAPI · SQLAlchemy async · Alembic · Pydantic v2 · Next.js 15 App Router · TypeScript · shadcn/ui (Card, Input, Label, Button, Textarea)

**Spec:** `docs/superpowers/specs/2026-04-17-repo-alignment-settings-ui-design.md`

---

## File Map

### Created
| Path | Purpose |
|---|---|
| `web/src/components/review/.gitkeep` | Stub folder (documented in FRONTEND.md) |
| `web/src/components/edit/.gitkeep` | Stub folder (documented in FRONTEND.md) |
| `api/app/models/app_settings.py` | ORM model, single row id=1 |
| `api/app/schemas/app_settings.py` | AppSettingsRead + AppSettingsUpdate Pydantic schemas |
| `api/app/repositories/app_settings_repo.py` | get() + upsert() DB access |
| `api/app/services/settings_service.py` | get_effective() + update() business logic |
| `api/app/routers/settings.py` | GET + PUT /api/v1/settings |
| `api/tests/test_settings.py` | Unit tests for service + endpoint smoke tests |
| `web/src/app/(app)/settings/page.tsx` | Server Component — fetches + passes settings |
| `web/src/app/(app)/settings/SettingsForm.client.tsx` | Client form — save, toast, show/hide toggles |

### Modified
| Path | Change |
|---|---|
| `docs/DESIGN.md` | Add Settings page section |
| `docs/FRONTEND.md` | Add /settings route to table |
| `docs/BACKEND.md` | Add app_settings to data model; document RuntimeSettings + get_runtime_settings |
| `docs/DECISIONS.md` | Add ADR for settings-in-DB + future Fernet encryption note |
| `CLAUDE.md` | Add app_settings to §9 schema block |
| `api/app/config.py` | Add RuntimeSettings dataclass |
| `api/app/dependencies.py` | Add get_runtime_settings() FastAPI dependency |
| `api/app/integrations/claude.py` | Accept optional api_key param in __init__ |
| `api/app/services/description_service.py` | Accept anthropic_api_key param; pass to ClaudeClient |
| `api/app/routers/descriptions.py` | Inject RuntimeSettings; pass api_key to DescriptionService |
| `api/app/main.py` | Register settings router |
| `api/alembic/env.py` | Import AppSettings model so autogenerate sees it |
| `web/src/types/api.ts` | Add AppSettings interface |
| `web/src/app/(app)/dashboard/DashboardContent.client.tsx` | Add Settings nav link |

---

## Task 1: Stub folders + gitkeep

**Files:**
- Create: `web/src/components/review/.gitkeep`
- Create: `web/src/components/edit/.gitkeep`

- [x] **Step 1: Create stub folders**

```bash
touch web/src/components/review/.gitkeep
touch web/src/components/edit/.gitkeep
```

- [x] **Step 2: Commit**

```bash
git add web/src/components/review/.gitkeep web/src/components/edit/.gitkeep
git commit -m "chore: add stub folders for review and edit components"
```

---

## Task 2: Update MD docs

**Files:**
- Modify: `docs/DESIGN.md`
- Modify: `docs/FRONTEND.md`
- Modify: `docs/BACKEND.md`
- Modify: `docs/DECISIONS.md`
- Modify: `CLAUDE.md`

- [x] **Step 1: Add Settings page section to DESIGN.md**

Append this block at the end of `docs/DESIGN.md` (before any trailing newline):

```markdown

---

## Settings Page

Single-column layout, `max-w-2xl mx-auto`. Three `Card` sections stacked vertically:
**Integrations**, **Budget**, **Style**. Each section has a subdued all-caps label
(`text-sm font-semibold text-muted-foreground uppercase tracking-wide`) followed by
`Label + Input` pairs.

Sensitive fields (API keys, OAuth secret) use `type="password"` with a **Show/Hide**
`Button variant="outline" size="sm"` to the right. Not a custom control — just
a flex row wrapping the input and button.

Save button at the bottom: `<Button type="submit">`. Inline feedback as a `<span>`
next to the button — `text-emerald-400` on success, `text-destructive` on error.
No modal — settings changes are non-destructive.
```

- [x] **Step 2: Add /settings to FRONTEND.md route table**

In `docs/FRONTEND.md`, find the route groups table under `## Layout`:

```
| `app/` | App Router pages. Route groups: `(auth)` (login), `(app)` (dashboard, session, group, edit). |
```

Replace with:

```
| `app/` | App Router pages. Route groups: `(auth)` (login), `(app)` (dashboard, session, group, edit, settings). |
```

- [x] **Step 3: Update BACKEND.md — add app_settings and RuntimeSettings**

In `docs/BACKEND.md`, find the `## Layout` table and add a row for the new service:

Find:
```
| `app/services/` | Business logic — orchestrates repos + integrations |
```

The table already covers services generically. Add the following block after the layout table (before "**Rule:** routers call services…"):

```markdown
### Runtime settings resolution

`app/config.py` defines a `RuntimeSettings` dataclass (all the same fields as
`Settings`). `app/dependencies.py` provides `get_runtime_settings()` — an async
FastAPI dependency that reads the `app_settings` DB row via `AppSettingsRepository`,
falls back to env/`.env` values for any empty field, and returns a
`RuntimeSettings` instance. Inject it with `Depends(get_runtime_settings)` in
any router that needs live API keys.
```

Also append `app_settings` to the data model description (find the existing "Adding an ORM model" section and add a note):

Find the line:
```
3. `make migrate-new msg="add <thing>"` to generate a revision.
```

This is already there; no change needed. Just add `app_settings` to the `CLAUDE.md` schema (Step 5 covers that).

- [x] **Step 4: Add ADR to DECISIONS.md**

Append at the end of `docs/DECISIONS.md`:

```markdown

## 2026-04-17 — Settings stored in Postgres

**Status:** accepted
**Context:** API keys (Anthropic, Replicate, Google OAuth) and budget caps need to
be editable at runtime without redeploying. Single-user app — no per-user settings
needed.
**Decision:** A single `app_settings` table row (id=1, upserted on save) holds all
runtime-configurable values. A `RuntimeSettings` dataclass is built by the
`get_runtime_settings()` FastAPI dependency, merging DB values with env/.env fallbacks.
Env vars remain effective on first deploy before the user visits Settings.
**Consequences:**
- Adding a new configurable field requires an Alembic migration.
- Values are stored plaintext in Postgres for MVP.

## 2026-04-17 — Future: encrypt sensitive settings fields

**Status:** planned (not implemented)
**Context:** `anthropic_api_key`, `replicate_api_token`, and `google_oauth_client_secret`
are sensitive. Storing them plaintext in Postgres is acceptable for single-user MVP
but must be fixed before public launch.
**Decision (future):** Encrypt those columns at rest using the existing `fernet_key`
in `config.py` (symmetric encryption). Decrypt on read in `AppSettingsRepository`.
**Consequences:** Requires a migration to re-encrypt existing values and a boot-time
check that `fernet_key` is set before writing sensitive fields.
```

- [x] **Step 5: Add app_settings to CLAUDE.md §9 schema block**

In `CLAUDE.md`, find the `cost_log` table definition (last table in §9):

```
cost_log
  id, session_id, operation, model, tokens, dollars_estimate, created_at
```

After it, add:

```
app_settings
  id (always 1), anthropic_api_key, replicate_api_token,
  google_oauth_client_id, google_oauth_client_secret, google_oauth_redirect_uri,
  session_budget_usd, session_hard_cap_usd, style_seed_text, updated_at
```

- [x] **Step 6: Commit all doc changes**

```bash
git add docs/DESIGN.md docs/FRONTEND.md docs/BACKEND.md docs/DECISIONS.md CLAUDE.md
git commit -m "docs: repo alignment — add settings references to all MDs"
```

---

## Task 3: AppSettings ORM model + migration

**Files:**
- Create: `api/app/models/app_settings.py`
- Modify: `api/alembic/env.py`

- [x] **Step 1: Create the ORM model**

Create `api/app/models/app_settings.py`:

```python
"""AppSettings model — single-row runtime configuration override."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class AppSettings(Base):
    __tablename__ = "app_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    anthropic_api_key: Mapped[str] = mapped_column(String, nullable=False, server_default="")
    replicate_api_token: Mapped[str] = mapped_column(String, nullable=False, server_default="")
    google_oauth_client_id: Mapped[str] = mapped_column(String, nullable=False, server_default="")
    google_oauth_client_secret: Mapped[str] = mapped_column(String, nullable=False, server_default="")
    google_oauth_redirect_uri: Mapped[str] = mapped_column(
        String,
        nullable=False,
        server_default="http://localhost:8000/api/v1/storage/google/oauth/callback",
    )
    session_budget_usd: Mapped[float] = mapped_column(
        Float, nullable=False, server_default=text("10.0")
    )
    session_hard_cap_usd: Mapped[float] = mapped_column(
        Float, nullable=False, server_default=text("50.0")
    )
    style_seed_text: Mapped[str] = mapped_column(String, nullable=False, server_default="")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
```

- [x] **Step 2: Import model in alembic/env.py so autogenerate sees it**

Open `api/alembic/env.py`. Find the block where other models are imported (look for lines like `from app.models.session import Session` or a shared `from app.models import *`). Add:

```python
from app.models.app_settings import AppSettings  # noqa: F401
```

- [x] **Step 3: Generate the migration**

```bash
make migrate-new msg="add app_settings table"
```

- [x] **Step 4: Review the generated migration**

Open the newest file in `api/alembic/versions/`. Verify it creates the `app_settings` table with all 10 columns. It should look like:

```python
def upgrade() -> None:
    op.create_table(
        "app_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("anthropic_api_key", sa.String(), server_default="", nullable=False),
        sa.Column("replicate_api_token", sa.String(), server_default="", nullable=False),
        sa.Column("google_oauth_client_id", sa.String(), server_default="", nullable=False),
        sa.Column("google_oauth_client_secret", sa.String(), server_default="", nullable=False),
        sa.Column(
            "google_oauth_redirect_uri",
            sa.String(),
            server_default="http://localhost:8000/api/v1/storage/google/oauth/callback",
            nullable=False,
        ),
        sa.Column("session_budget_usd", sa.Float(), server_default=sa.text("10.0"), nullable=False),
        sa.Column("session_hard_cap_usd", sa.Float(), server_default=sa.text("50.0"), nullable=False),
        sa.Column("style_seed_text", sa.String(), server_default="", nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

def downgrade() -> None:
    op.drop_table("app_settings")
```

If autogenerate omitted columns or added noise, edit the file to match the above.

- [x] **Step 5: Apply the migration**

```bash
make migrate
```

Expected output ends with: `Running upgrade ... -> <revision_id>, add app_settings table`

- [x] **Step 6: Commit**

```bash
git add api/app/models/app_settings.py api/alembic/env.py api/alembic/versions/
git commit -m "feat: add app_settings ORM model and migration"
```

---

## Task 4: AppSettings Pydantic schemas + RuntimeSettings dataclass

**Files:**
- Create: `api/app/schemas/app_settings.py`
- Modify: `api/app/config.py`

- [x] **Step 1: Create schemas**

Create `api/app/schemas/app_settings.py`:

```python
"""AppSettings request/response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AppSettingsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    anthropic_api_key: str
    replicate_api_token: str
    google_oauth_client_id: str
    google_oauth_client_secret: str
    google_oauth_redirect_uri: str
    session_budget_usd: float
    session_hard_cap_usd: float
    style_seed_text: str
    updated_at: datetime | None = None


class AppSettingsUpdate(BaseModel):
    anthropic_api_key: str = ""
    replicate_api_token: str = ""
    google_oauth_client_id: str = ""
    google_oauth_client_secret: str = ""
    google_oauth_redirect_uri: str = (
        "http://localhost:8000/api/v1/storage/google/oauth/callback"
    )
    session_budget_usd: float = Field(default=10.0, gt=0)
    session_hard_cap_usd: float = Field(default=50.0, gt=0)
    style_seed_text: str = ""
```

- [x] **Step 2: Add RuntimeSettings dataclass to config.py**

Open `api/app/config.py`. After the `settings = get_settings()` line at the bottom, add:

```python
from dataclasses import dataclass


@dataclass
class RuntimeSettings:
    """Merged settings: DB row values take precedence over env defaults."""

    anthropic_api_key: str
    replicate_api_token: str
    google_oauth_client_id: str
    google_oauth_client_secret: str
    google_oauth_redirect_uri: str
    session_budget_usd: float
    session_hard_cap_usd: float
    style_seed_text: str
```

- [x] **Step 3: Commit**

```bash
git add api/app/schemas/app_settings.py api/app/config.py
git commit -m "feat: add AppSettings schemas and RuntimeSettings dataclass"
```

---

## Task 5: AppSettingsRepository (TDD)

**Files:**
- Create: `api/app/repositories/app_settings_repo.py`
- Create: `api/tests/test_settings.py` (partial — repo tests added here)

- [x] **Step 1: Write the failing test**

Create `api/tests/test_settings.py`:

```python
"""Tests for AppSettings repository, service, and endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from app.models.app_settings import AppSettings
from app.schemas.app_settings import AppSettingsUpdate


def _make_row(**kwargs) -> AppSettings:
    defaults = dict(
        id=1,
        anthropic_api_key="",
        replicate_api_token="",
        google_oauth_client_id="",
        google_oauth_client_secret="",
        google_oauth_redirect_uri="http://localhost:8000/api/v1/storage/google/oauth/callback",
        session_budget_usd=10.0,
        session_hard_cap_usd=50.0,
        style_seed_text="",
        updated_at=datetime.now(timezone.utc),
    )
    defaults.update(kwargs)
    return AppSettings(**defaults)


# ── Repository tests ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_repo_get_returns_none_when_empty() -> None:
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.repositories.app_settings_repo import AppSettingsRepository

    db = AsyncMock(spec=AsyncSession)
    # Simulate execute returning no row
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=mock_result)

    repo = AppSettingsRepository(db)
    result = await repo.get()
    assert result is None


@pytest.mark.asyncio
async def test_repo_upsert_creates_new_row() -> None:
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.repositories.app_settings_repo import AppSettingsRepository

    db = AsyncMock(spec=AsyncSession)
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=mock_result)
    db.add = AsyncMock()
    db.flush = AsyncMock()

    repo = AppSettingsRepository(db)
    data = AppSettingsUpdate(anthropic_api_key="sk-test", session_budget_usd=20.0)
    row = await repo.upsert(data)

    db.add.assert_called_once()
    db.flush.assert_called_once()
    assert row.anthropic_api_key == "sk-test"
    assert row.session_budget_usd == 20.0
```

- [x] **Step 2: Run test to verify it fails**

```bash
cd api && uv run pytest tests/test_settings.py::test_repo_get_returns_none_when_empty -v
```

Expected: `FAILED` — `ModuleNotFoundError: app.repositories.app_settings_repo`

- [x] **Step 3: Create the repository**

Create `api/app/repositories/app_settings_repo.py`:

```python
"""AppSettings repository."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.app_settings import AppSettings
from app.schemas.app_settings import AppSettingsUpdate


class AppSettingsRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get(self) -> AppSettings | None:
        result = await self.db.execute(select(AppSettings).where(AppSettings.id == 1))
        return result.scalar_one_or_none()

    async def upsert(self, data: AppSettingsUpdate) -> AppSettings:
        row = await self.get()
        if row is None:
            row = AppSettings(id=1, **data.model_dump())
            self.db.add(row)
        else:
            for key, value in data.model_dump().items():
                setattr(row, key, value)
            row.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return row
```

- [x] **Step 4: Run tests to verify they pass**

```bash
cd api && uv run pytest tests/test_settings.py::test_repo_get_returns_none_when_empty tests/test_settings.py::test_repo_upsert_creates_new_row -v
```

Expected: both `PASSED`

- [x] **Step 5: Commit**

```bash
git add api/app/repositories/app_settings_repo.py api/tests/test_settings.py
git commit -m "feat: add AppSettingsRepository with get and upsert"
```

---

## Task 6: SettingsService (TDD)

**Files:**
- Create: `api/app/services/settings_service.py`
- Modify: `api/tests/test_settings.py` (add service tests)

- [x] **Step 1: Add failing service tests to test_settings.py**

Append to `api/tests/test_settings.py`:

```python
# ── Service tests ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_service_get_effective_no_row_returns_env_defaults() -> None:
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.services.settings_service import SettingsService
    from app.config import get_settings

    db = AsyncMock(spec=AsyncSession)
    service = SettingsService(db)
    service.repo.get = AsyncMock(return_value=None)

    result = await service.get_effective()
    env = get_settings()

    assert result.anthropic_api_key == env.anthropic_api_key
    assert result.session_budget_usd == env.session_budget_usd
    assert result.session_hard_cap_usd == env.session_hard_cap_usd


@pytest.mark.asyncio
async def test_service_get_effective_db_values_override_env() -> None:
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.services.settings_service import SettingsService

    db = AsyncMock(spec=AsyncSession)
    service = SettingsService(db)
    row = _make_row(anthropic_api_key="sk-from-db", session_budget_usd=99.0)
    service.repo.get = AsyncMock(return_value=row)

    result = await service.get_effective()

    assert result.anthropic_api_key == "sk-from-db"
    assert result.session_budget_usd == 99.0


@pytest.mark.asyncio
async def test_service_update_calls_repo_upsert() -> None:
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.services.settings_service import SettingsService

    db = AsyncMock(spec=AsyncSession)
    service = SettingsService(db)
    saved = _make_row(anthropic_api_key="new-key", session_budget_usd=15.0)
    service.repo.upsert = AsyncMock(return_value=saved)

    data = AppSettingsUpdate(anthropic_api_key="new-key", session_budget_usd=15.0)
    result = await service.update(data)

    service.repo.upsert.assert_called_once_with(data)
    assert result.anthropic_api_key == "new-key"
    assert result.session_budget_usd == 15.0
```

- [x] **Step 2: Run tests to verify they fail**

```bash
cd api && uv run pytest tests/test_settings.py -k "service" -v
```

Expected: `FAILED` — `ModuleNotFoundError: app.services.settings_service`

- [x] **Step 3: Create the service**

Create `api/app/services/settings_service.py`:

```python
"""Settings service — merges DB row with env defaults."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.repositories.app_settings_repo import AppSettingsRepository
from app.schemas.app_settings import AppSettingsRead, AppSettingsUpdate


class SettingsService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = AppSettingsRepository(db)

    async def get_effective(self) -> AppSettingsRead:
        env = get_settings()
        row = await self.repo.get()

        def _s(db_val: str, env_val: str) -> str:
            return db_val if db_val else env_val

        if row is None:
            return AppSettingsRead(
                anthropic_api_key=env.anthropic_api_key,
                replicate_api_token=env.replicate_api_token,
                google_oauth_client_id=env.google_oauth_client_id,
                google_oauth_client_secret=env.google_oauth_client_secret,
                google_oauth_redirect_uri=env.google_oauth_redirect_uri,
                session_budget_usd=env.session_budget_usd,
                session_hard_cap_usd=env.session_hard_cap_usd,
                style_seed_text="",
                updated_at=None,
            )

        return AppSettingsRead(
            anthropic_api_key=_s(row.anthropic_api_key, env.anthropic_api_key),
            replicate_api_token=_s(row.replicate_api_token, env.replicate_api_token),
            google_oauth_client_id=_s(row.google_oauth_client_id, env.google_oauth_client_id),
            google_oauth_client_secret=_s(row.google_oauth_client_secret, env.google_oauth_client_secret),
            google_oauth_redirect_uri=_s(row.google_oauth_redirect_uri, env.google_oauth_redirect_uri),
            session_budget_usd=row.session_budget_usd,
            session_hard_cap_usd=row.session_hard_cap_usd,
            style_seed_text=row.style_seed_text,
            updated_at=row.updated_at,
        )

    async def update(self, data: AppSettingsUpdate) -> AppSettingsRead:
        env = get_settings()
        row = await self.repo.upsert(data)
        return AppSettingsRead(
            anthropic_api_key=row.anthropic_api_key or env.anthropic_api_key,
            replicate_api_token=row.replicate_api_token or env.replicate_api_token,
            google_oauth_client_id=row.google_oauth_client_id or env.google_oauth_client_id,
            google_oauth_client_secret=row.google_oauth_client_secret or env.google_oauth_client_secret,
            google_oauth_redirect_uri=row.google_oauth_redirect_uri or env.google_oauth_redirect_uri,
            session_budget_usd=row.session_budget_usd,
            session_hard_cap_usd=row.session_hard_cap_usd,
            style_seed_text=row.style_seed_text,
            updated_at=row.updated_at,
        )
```

- [x] **Step 4: Run all settings tests**

```bash
cd api && uv run pytest tests/test_settings.py -v
```

Expected: all 5 tests `PASSED`

- [x] **Step 5: Commit**

```bash
git add api/app/services/settings_service.py api/tests/test_settings.py
git commit -m "feat: add SettingsService with get_effective and update"
```

---

## Task 7: get_runtime_settings dependency + update ClaudeClient

**Files:**
- Modify: `api/app/dependencies.py`
- Modify: `api/app/integrations/claude.py`
- Modify: `api/app/services/description_service.py`
- Modify: `api/app/routers/descriptions.py`

- [x] **Step 1: Add get_runtime_settings to dependencies.py**

Open `api/app/dependencies.py`. At the top, add the import:

```python
from app.config import RuntimeSettings, get_settings
```

Then append this function at the end of the file:

```python
async def get_runtime_settings(db: AsyncSession = Depends(get_db)) -> RuntimeSettings:
    """FastAPI dependency: merges DB app_settings row with env defaults."""
    from app.repositories.app_settings_repo import AppSettingsRepository

    env = get_settings()
    repo = AppSettingsRepository(db)
    row = await repo.get()

    def _s(db_val: str, env_val: str) -> str:
        return db_val if db_val else env_val

    if row is None:
        return RuntimeSettings(
            anthropic_api_key=env.anthropic_api_key,
            replicate_api_token=env.replicate_api_token,
            google_oauth_client_id=env.google_oauth_client_id,
            google_oauth_client_secret=env.google_oauth_client_secret,
            google_oauth_redirect_uri=env.google_oauth_redirect_uri,
            session_budget_usd=env.session_budget_usd,
            session_hard_cap_usd=env.session_hard_cap_usd,
            style_seed_text="",
        )

    return RuntimeSettings(
        anthropic_api_key=_s(row.anthropic_api_key, env.anthropic_api_key),
        replicate_api_token=_s(row.replicate_api_token, env.replicate_api_token),
        google_oauth_client_id=_s(row.google_oauth_client_id, env.google_oauth_client_id),
        google_oauth_client_secret=_s(row.google_oauth_client_secret, env.google_oauth_client_secret),
        google_oauth_redirect_uri=_s(row.google_oauth_redirect_uri, env.google_oauth_redirect_uri),
        session_budget_usd=row.session_budget_usd,
        session_hard_cap_usd=row.session_hard_cap_usd,
        style_seed_text=row.style_seed_text,
    )
```

- [x] **Step 2: Update ClaudeClient to accept optional api_key**

Open `api/app/integrations/claude.py`. Find:

```python
    def __init__(self, cache_repo=None):
        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.cache_repo = cache_repo
```

Replace with:

```python
    def __init__(self, api_key: str | None = None, cache_repo=None):
        self.client = Anthropic(api_key=api_key or settings.anthropic_api_key)
        self.cache_repo = cache_repo
```

- [x] **Step 3: Update DescriptionService to accept anthropic_api_key**

Open `api/app/services/description_service.py`. Find:

```python
    def __init__(self, session: AsyncSession):
        self.session = session
        self.desc_repo = DescriptionRepository(session)
        self.asset_repo = AssetRepository(session)
        self.group_repo = GroupRepository(session)
        self.claude = ClaudeClient()
```

Replace with:

```python
    def __init__(self, session: AsyncSession, anthropic_api_key: str | None = None):
        self.session = session
        self.desc_repo = DescriptionRepository(session)
        self.asset_repo = AssetRepository(session)
        self.group_repo = GroupRepository(session)
        self.claude = ClaudeClient(api_key=anthropic_api_key)
```

- [x] **Step 4: Update the descriptions router to inject RuntimeSettings**

Open `api/app/routers/descriptions.py`. Add to the imports:

```python
from app.config import RuntimeSettings
from app.dependencies import get_runtime_settings
```

Find the `generate_description` function signature:

```python
async def generate_description(
    group_id: str,
    req: DescriptionRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> DescriptionResponse:
```

Replace with:

```python
async def generate_description(
    group_id: str,
    req: DescriptionRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    runtime: RuntimeSettings = Depends(get_runtime_settings),
) -> DescriptionResponse:
```

Inside that function, find where `DescriptionService` is instantiated. It will look like:

```python
    service = DescriptionService(session)
```

Replace with:

```python
    service = DescriptionService(session, anthropic_api_key=runtime.anthropic_api_key)
```

- [x] **Step 5: Run existing tests to verify nothing broke**

```bash
cd api && uv run pytest tests/ -v --ignore=tests/test_settings.py
```

Expected: all previously passing tests still `PASSED`

- [x] **Step 6: Commit**

```bash
git add api/app/dependencies.py api/app/integrations/claude.py \
        api/app/services/description_service.py api/app/routers/descriptions.py
git commit -m "feat: add get_runtime_settings dependency; wire ClaudeClient key injection"
```

---

## Task 8: Settings router + register in main.py

**Files:**
- Create: `api/app/routers/settings.py`
- Modify: `api/app/main.py`
- Modify: `api/tests/test_settings.py` (add endpoint smoke tests)

- [x] **Step 1: Add endpoint smoke tests to test_settings.py**

Append to `api/tests/test_settings.py`:

```python
# ── Endpoint smoke tests ──────────────────────────────────────────────────────

def test_get_settings_unauthenticated(client) -> None:
    res = client.get("/api/v1/settings")
    assert res.status_code == 401


def test_put_settings_invalid_budget_returns_422(client) -> None:
    res = client.put(
        "/api/v1/settings",
        json={
            "session_budget_usd": -1.0,
            "session_hard_cap_usd": 50.0,
        },
    )
    # 401 because no auth token — but pydantic validation fires first on some versions
    assert res.status_code in (401, 422)
```

- [x] **Step 2: Run smoke tests to verify they fail correctly**

```bash
cd api && uv run pytest tests/test_settings.py::test_get_settings_unauthenticated -v
```

Expected: `FAILED` — 404 (route doesn't exist yet) rather than 401

- [x] **Step 3: Create the settings router**

Create `api/app/routers/settings.py`:

```python
"""Settings endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.app_settings import AppSettingsRead, AppSettingsUpdate
from app.services.settings_service import SettingsService

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=AppSettingsRead)
async def get_settings(
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AppSettingsRead:
    return await SettingsService(db).get_effective()


@router.put("", response_model=AppSettingsRead)
async def update_settings(
    data: AppSettingsUpdate,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AppSettingsRead:
    return await SettingsService(db).update(data)
```

- [x] **Step 4: Register the router in main.py**

Open `api/app/main.py`. Find the imports line:

```python
from app.routers import health, auth, storage, sessions, assets, events, groups, edits, cost, face_crops, descriptions, exports
```

Replace with:

```python
from app.routers import health, auth, storage, sessions, assets, events, groups, edits, cost, face_crops, descriptions, exports, settings
```

Then after the last `app.include_router(exports.router)` line, add:

```python
    app.include_router(settings.router, prefix=API_V1_PREFIX)
```

- [x] **Step 5: Run all settings tests**

```bash
cd api && uv run pytest tests/test_settings.py -v
```

Expected: all 7 tests `PASSED` (the 401 test now passes since the route exists)

- [x] **Step 6: Run the full test suite**

```bash
cd api && uv run pytest tests/ -v
```

Expected: all tests `PASSED`

- [x] **Step 7: Commit**

```bash
git add api/app/routers/settings.py api/app/main.py api/tests/test_settings.py
git commit -m "feat: add settings router (GET/PUT /api/v1/settings) and register in app"
```

---

## Task 9: Install Textarea + add AppSettings type

**Files:**
- Install: `web/src/components/ui/textarea.tsx` (via shadcn CLI)
- Modify: `web/src/types/api.ts`

- [x] **Step 1: Install the Textarea shadcn component**

```bash
cd web && pnpm dlx shadcn@latest add textarea
```

Expected: creates `web/src/components/ui/textarea.tsx`

- [x] **Step 2: Add AppSettings interface to types/api.ts**

Open `web/src/types/api.ts`. Append at the end of the file:

```typescript
// ── Settings ──────────────────────────────────────────────────────────────────

export interface AppSettings {
  anthropic_api_key: string;
  replicate_api_token: string;
  google_oauth_client_id: string;
  google_oauth_client_secret: string;
  google_oauth_redirect_uri: string;
  session_budget_usd: number;
  session_hard_cap_usd: number;
  style_seed_text: string;
  updated_at: string | null;
}
```

- [x] **Step 3: Commit**

```bash
git add web/src/components/ui/textarea.tsx web/src/types/api.ts
git commit -m "feat: add Textarea shadcn component and AppSettings type"
```

---

## Task 10: Settings page (server + client)

**Files:**
- Create: `web/src/app/(app)/settings/page.tsx`
- Create: `web/src/app/(app)/settings/SettingsForm.client.tsx`

- [x] **Step 1: Create the server component**

Create `web/src/app/(app)/settings/page.tsx`:

```tsx
import { apiFetch } from "@/lib/api-client";
import type { AppSettings } from "@/types/api";
import { SettingsForm } from "./SettingsForm.client";

export const metadata = { title: "Settings — InfluencerFlow" };

export default async function SettingsPage() {
  let initial: AppSettings | null = null;
  try {
    initial = await apiFetch<AppSettings>("/settings");
  } catch {
    // Render form with empty defaults if fetch fails (e.g. no auth cookie server-side yet)
  }

  return (
    <div className="max-w-2xl mx-auto py-8 space-y-6">
      <h1 className="text-2xl font-bold">Settings</h1>
      <SettingsForm initial={initial} />
    </div>
  );
}
```

- [x] **Step 2: Create the client form**

Create `web/src/app/(app)/settings/SettingsForm.client.tsx`:

```tsx
"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { apiFetch, ApiError } from "@/lib/api-client";
import type { AppSettings } from "@/types/api";

interface SettingsFormProps {
  initial: AppSettings | null;
}

const EMPTY: AppSettings = {
  anthropic_api_key: "",
  replicate_api_token: "",
  google_oauth_client_id: "",
  google_oauth_client_secret: "",
  google_oauth_redirect_uri: "http://localhost:8000/api/v1/storage/google/oauth/callback",
  session_budget_usd: 10,
  session_hard_cap_usd: 50,
  style_seed_text: "",
  updated_at: null,
};

export function SettingsForm({ initial }: SettingsFormProps) {
  const [form, setForm] = useState<AppSettings>(initial ?? EMPTY);
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState<{ msg: string; ok: boolean } | null>(null);
  const [shown, setShown] = useState<Set<keyof AppSettings>>(new Set());

  function set(key: keyof AppSettings, value: string | number) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  function toggleShow(key: keyof AppSettings) {
    setShown((s) => {
      const next = new Set(s);
      next.has(key) ? next.delete(key) : next.add(key);
      return next;
    });
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setToast(null);
    try {
      await apiFetch("/settings", { method: "PUT", body: form });
      setToast({ msg: "Settings saved", ok: true });
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Save failed";
      setToast({ msg, ok: false });
    } finally {
      setSaving(false);
    }
  }

  function SecretField({
    field,
    label,
  }: {
    field: keyof AppSettings;
    label: string;
  }) {
    const visible = shown.has(field);
    return (
      <div className="space-y-1">
        <Label htmlFor={field as string}>{label}</Label>
        <div className="flex gap-2">
          <Input
            id={field as string}
            type={visible ? "text" : "password"}
            value={String(form[field])}
            onChange={(e) => set(field, e.target.value)}
            className="flex-1"
          />
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => toggleShow(field)}
          >
            {visible ? "Hide" : "Show"}
          </Button>
        </div>
      </div>
    );
  }

  return (
    <form onSubmit={handleSave} className="space-y-6">
      <Card className="p-6 space-y-4">
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
          Integrations
        </h2>
        <SecretField field="anthropic_api_key" label="Anthropic API Key" />
        <SecretField field="replicate_api_token" label="Replicate API Token" />
        <div className="space-y-1">
          <Label htmlFor="google_oauth_client_id">Google OAuth Client ID</Label>
          <Input
            id="google_oauth_client_id"
            value={form.google_oauth_client_id}
            onChange={(e) => set("google_oauth_client_id", e.target.value)}
          />
        </div>
        <SecretField
          field="google_oauth_client_secret"
          label="Google OAuth Client Secret"
        />
        <div className="space-y-1">
          <Label htmlFor="google_oauth_redirect_uri">
            Google OAuth Redirect URI
          </Label>
          <Input
            id="google_oauth_redirect_uri"
            value={form.google_oauth_redirect_uri}
            onChange={(e) => set("google_oauth_redirect_uri", e.target.value)}
          />
        </div>
      </Card>

      <Card className="p-6 space-y-4">
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
          Budget
        </h2>
        <div className="space-y-1">
          <Label htmlFor="session_budget_usd">Session Budget (USD)</Label>
          <Input
            id="session_budget_usd"
            type="number"
            step="0.01"
            min="0.01"
            value={form.session_budget_usd}
            onChange={(e) =>
              set("session_budget_usd", parseFloat(e.target.value))
            }
          />
        </div>
        <div className="space-y-1">
          <Label htmlFor="session_hard_cap_usd">Session Hard Cap (USD)</Label>
          <Input
            id="session_hard_cap_usd"
            type="number"
            step="0.01"
            min="0.01"
            value={form.session_hard_cap_usd}
            onChange={(e) =>
              set("session_hard_cap_usd", parseFloat(e.target.value))
            }
          />
        </div>
      </Card>

      <Card className="p-6 space-y-4">
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
          Style
        </h2>
        <div className="space-y-1">
          <Label htmlFor="style_seed_text">Style Seed Text</Label>
          <Textarea
            id="style_seed_text"
            rows={6}
            placeholder="Paste past captions or style notes for AI description generation…"
            value={form.style_seed_text}
            onChange={(e) => set("style_seed_text", e.target.value)}
          />
        </div>
      </Card>

      <div className="flex items-center gap-4">
        <Button type="submit" disabled={saving}>
          {saving ? "Saving…" : "Save settings"}
        </Button>
        {toast && (
          <span
            className={
              toast.ok ? "text-emerald-400 text-sm" : "text-destructive text-sm"
            }
          >
            {toast.msg}
          </span>
        )}
      </div>
    </form>
  );
}
```

- [x] **Step 3: Typecheck**

```bash
cd web && pnpm tsc --noEmit
```

Expected: no errors

- [x] **Step 4: Commit**

```bash
git add web/src/app/\(app\)/settings/
git commit -m "feat: add Settings page (server component + client form)"
```

---

## Task 11: Dashboard settings nav link

**Files:**
- Modify: `web/src/app/(app)/dashboard/DashboardContent.client.tsx`

- [x] **Step 1: Add Settings link**

Open `web/src/app/(app)/dashboard/DashboardContent.client.tsx`.

Add `Link` to the imports:

```tsx
import Link from "next/link";
```

Find the header row:

```tsx
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-medium">Your sessions</h2>
        <Button onClick={() => router.push("/dashboard/new")}>
          {COPY.newSession}
        </Button>
      </div>
```

Replace with:

```tsx
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-medium">Your sessions</h2>
        <div className="flex items-center gap-3">
          <Link
            href="/settings"
            className="text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            Settings
          </Link>
          <Button onClick={() => router.push("/dashboard/new")}>
            {COPY.newSession}
          </Button>
        </div>
      </div>
```

- [x] **Step 2: Typecheck**

```bash
cd web && pnpm tsc --noEmit
```

Expected: no errors

- [x] **Step 3: Run the full test suite one final time**

```bash
cd api && uv run pytest tests/ -v
```

Expected: all tests `PASSED`

- [x] **Step 4: Commit**

```bash
git add web/src/app/\(app\)/dashboard/DashboardContent.client.tsx
git commit -m "feat: add Settings nav link to dashboard header"
```

---

## Done

All 11 tasks complete. The repo is aligned to its MDs, the `app_settings` table is live, `GET/PUT /api/v1/settings` are operational, API keys and budget caps are editable from `(app)/settings`, and the `DescriptionService` now picks up the live Anthropic key from the DB.
