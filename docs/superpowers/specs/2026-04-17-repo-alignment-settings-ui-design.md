# Repo Alignment + Settings UI — Design Spec

**Date:** 2026-04-17
**Status:** approved
**Scope:** Two sequential tasks — (1) align repo to existing MDs, (2) implement a Settings page backed by a DB row.

---

## 1. Repo Alignment

### Goal
Make every claim in the MD docs (`FRONTEND.md`, `BACKEND.md`, `DESIGN.md`, `CLAUDE.md`) verifiable by looking at the code. No phantom folders, no undocumented files.

### Gaps to close

| Gap | Action |
|---|---|
| `web/src/components/review/` missing | Create folder + `.gitkeep` |
| `web/src/components/edit/` missing | Create folder + `.gitkeep` |
| `web/src/lib/api-client.ts` — verify exists, create stub if not | Verify / create |
| `web/src/lib/utils.ts` — verify exists, create stub if not | Verify / create |
| `DESIGN.md` — no Settings page section | Add section (see §4 below) |
| `FRONTEND.md` route table — no `/settings` entry | Add entry |
| `BACKEND.md` — `app_settings` table not listed | Add to data model section |
| `DECISIONS.md` — no ADR for settings storage | Add ADR entry |

No structural refactoring. Existing folder layout already matches the MDs.

---

## 2. Data Model

New table `app_settings` — always exactly one row (`id = 1`), upserted on save.

```sql
CREATE TABLE app_settings (
  id                        INTEGER PRIMARY KEY DEFAULT 1,
  anthropic_api_key         TEXT    NOT NULL DEFAULT '',
  replicate_api_token       TEXT    NOT NULL DEFAULT '',
  google_oauth_client_id    TEXT    NOT NULL DEFAULT '',
  google_oauth_client_secret TEXT   NOT NULL DEFAULT '',
  google_oauth_redirect_uri TEXT    NOT NULL DEFAULT 'http://localhost:8000/api/v1/storage/google/oauth/callback',
  session_budget_usd        FLOAT   NOT NULL DEFAULT 10.0,
  session_hard_cap_usd      FLOAT   NOT NULL DEFAULT 50.0,
  style_seed_text           TEXT    NOT NULL DEFAULT '',
  updated_at                TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

**Runtime resolution order:** DB row → env / `.env` file → hardcoded defaults.
Env vars remain functional on a fresh deploy before the user visits Settings.

**`style_seed_text` vs `api/assets/style_seed.txt`:** The DB field takes
precedence. `description_service.py` checks `style_seed_text` first; if empty,
it falls back to the file. This preserves the existing seed file as a
deploy-time default without breaking anything.

**Future improvement (to be tracked in `DECISIONS.md`):** encrypt sensitive
columns (`anthropic_api_key`, `replicate_api_token`, `google_oauth_client_secret`)
using the existing `fernet_key` before the app goes multi-user or public.

---

## 3. Backend

Follows the `BACKEND.md` layering rule: routers → services → repos → DB.

### New files

| File | Purpose |
|---|---|
| `api/app/models/app_settings.py` | ORM model; `id` defaults to 1 |
| `api/app/schemas/app_settings.py` | `AppSettingsRead` + `AppSettingsUpdate` Pydantic schemas |
| `api/app/repositories/app_settings_repo.py` | `get() → AppSettings \| None`, `upsert(data) → AppSettings` |
| `api/app/services/settings_service.py` | `get_effective()` merges DB row with env fallback; `update()` calls repo |
| `api/app/routers/settings.py` | Two endpoints (see below) |

### Endpoints

```
GET  /api/v1/settings        → AppSettingsRead   (current effective values)
PUT  /api/v1/settings        → AppSettingsRead   (validate + upsert, return saved)
```

Both endpoints require auth (existing JWT dependency).

### `config.py` change

Add `get_runtime_settings()` — an async FastAPI dependency that reads from DB
first, falls back to the pydantic `Settings` singleton. The following services
switch to this dependency: `description_service.py` (Anthropic key),
`editing_service.py` (Replicate token), and the Google Drive integration in
`app/integrations/` (OAuth credentials).

### Migration

```bash
make migrate-new msg="add app_settings table"
# review generated file in api/alembic/versions/
make migrate
```

### Tests

`api/tests/test_settings.py` — cover GET (no row → env defaults), PUT (valid
payload saves), PUT (invalid float → 422).

---

## 4. Frontend

Follows `FRONTEND.md` conventions and `DESIGN.md` visual system.

### New files

| File | Purpose |
|---|---|
| `web/src/app/(app)/settings/page.tsx` | Server Component; fetches settings via `apiFetch`, passes to form |
| `web/src/app/(app)/settings/SettingsForm.client.tsx` | `"use client"` form; handles save, toast feedback |

### Form structure

Three sections inside a single `Card`:

**Integrations**
- Anthropic API Key (`type="password"` + show/hide toggle)
- Replicate API Token (`type="password"` + show/hide toggle)
- Google OAuth Client ID
- Google OAuth Client Secret (`type="password"` + show/hide toggle)
- Google OAuth Redirect URI

**Budget**
- Session Budget USD (number input)
- Session Hard Cap USD (number input)

**Style**
- Style Seed Text (textarea — caption personality / past captions sample)

### Save flow

`PUT /api/v1/settings` on form submit → success toast "Settings saved" |
error toast with server message. No confirmation modal — settings are not
destructive.

### Nav link

Add a `Settings` link to the dashboard header pointing to `/settings`.
No new layout component — single anchor in the existing header chrome.

### shadcn components used

`Card`, `Input`, `Label`, `Button` — already present under
`web/src/components/ui/`. `Textarea` is not yet installed — run:

```bash
cd web && pnpm dlx shadcn@latest add textarea
```

---

## 5. MD Updates Required

As part of this work the following docs must be updated (not just code):

| Doc | Change |
|---|---|
| `docs/DESIGN.md` | Add "Settings page" section: calm single-column form, three card sections, password show/hide pattern |
| `docs/FRONTEND.md` | Add `/settings` to the route table |
| `docs/BACKEND.md` | Add `app_settings` to the data model listing; add `settings_service.py` and `get_runtime_settings()` to the conventions |
| `docs/DECISIONS.md` | Add ADR for settings-in-DB choice and future Fernet encryption note |
| `CLAUDE.md` (§9 Data Model) | Add `app_settings` table to the schema block |

---

## 6. Out of Scope

- Fernet encryption of sensitive columns (future, noted in DECISIONS.md)
- Per-session override of settings
- Settings export / import
- Audit log of settings changes
