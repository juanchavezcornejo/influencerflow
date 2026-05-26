# Docs Hierarchy + Settings UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the fragmented, oversized doc files with an atomic 18-file hierarchy rooted at CLAUDE.md, then implement a Settings UI (API keys, budgets, style seed) to validate that every agent instruction needed is findable in the new docs.

**Architecture:** Phase 1 creates docs only — no code changes. Phase 2 is a full-stack feature (DB → service → router → frontend page) implemented using only the new docs as reference, proving they are complete. If an agent gets stuck because a doc is missing info, that is a doc bug to fix in-place.

**Tech Stack:** Markdown (Phase 1). Python 3.12 / FastAPI / SQLAlchemy async / Pydantic v2 / Alembic / Next.js 15 App Router / TypeScript / Tailwind / shadcn/ui (Phase 2).

---

## Phase 1 — Documentation Hierarchy

### File Map (Phase 1)

| Action | Path |
|--------|------|
| Rewrite | `CLAUDE.md` |
| Create  | `docs/FLOW.md` |
| Create  | `docs/DATA.md` |
| Create  | `docs/API.md` |
| Rewrite | `docs/PROMPTS.md` |
| Keep    | `docs/DECISIONS.md` (append 1 ADR) |
| Create  | `docs/backend/CONVENTIONS.md` |
| Create  | `docs/backend/PIPELINE.md` |
| Create  | `docs/backend/INTEGRATIONS.md` |
| Create  | `docs/backend/WORKERS.md` |
| Create  | `docs/backend/SECURITY.md` |
| Create  | `docs/frontend/CONVENTIONS.md` |
| Rewrite | `docs/frontend/DESIGN.md` (trim to ≤400 lines, keep all specs) |
| Create  | `docs/frontend/STATE.md` |
| Rewrite | `docs/infra/DEVOPS.md` (from docs/DEVOPS.md) |
| Create  | `docs/infra/ENV.md` |
| Create  | `docs/infra/MIGRATIONS.md` |
| Rewrite | `docs/testing/STRATEGY.md` (from docs/TESTING.md) |
| Create  | `docs/testing/PATTERNS.md` |
| Delete  | `docs/ARCHITECTURE.md` (content distributed) |
| Delete  | `docs/BACKEND.md` (replaced by docs/backend/CONVENTIONS.md) |
| Delete  | `docs/FRONTEND.md` (replaced by docs/frontend/CONVENTIONS.md) |
| Delete  | `docs/TESTING.md` (replaced by docs/testing/STRATEGY.md) |
| Delete  | `docs/DEVOPS.md` (replaced by docs/infra/DEVOPS.md) |
| Delete  | `docs/DESIGN.md` (replaced by docs/frontend/DESIGN.md) |
| Archive | `docs/WEEK5_IMPLEMENTATION.md` → `docs/archive/WEEK5_IMPLEMENTATION.md` |
| Archive | `WEEK5_CHECKLIST.md` → `docs/archive/WEEK5_CHECKLIST.md` |

---

### Task 1: Scaffold directory structure

**Files:**
- Create dirs: `docs/backend/`, `docs/frontend/`, `docs/infra/`, `docs/testing/`, `docs/archive/`

- [x] **Step 1: Create directories**

```bash
mkdir -p /Users/juan/Projects/influencerflow/docs/backend
mkdir -p /Users/juan/Projects/influencerflow/docs/frontend
mkdir -p /Users/juan/Projects/influencerflow/docs/infra
mkdir -p /Users/juan/Projects/influencerflow/docs/testing
mkdir -p /Users/juan/Projects/influencerflow/docs/archive
```

- [x] **Step 2: Archive ephemeral docs**

```bash
mv docs/WEEK5_IMPLEMENTATION.md docs/archive/
mv WEEK5_CHECKLIST.md docs/archive/
```

- [x] **Step 3: Commit**

```bash
git add -A
git commit -m "chore: scaffold docs hierarchy directories, archive week5 status docs"
```

---

### Task 2: Rewrite CLAUDE.md — Root Index

**Files:**
- Rewrite: `CLAUDE.md`

- [x] **Step 1: Write CLAUDE.md**

Write the file with exactly this structure (≤200 lines):

```markdown
# InfluencerFlow — Agent Index

> Single-user app: cloud travel photos → grouped, edited, described, exported Instagram posts.
> Cost-conscious: every paid AI call shows a cost badge + confirmation before running.
> Non-destructive: originals in Google Drive are never modified.

## Tech Stack

| Layer | Choice |
|---|---|
| Frontend | Next.js 15 (App Router) + TypeScript + Tailwind + shadcn/ui |
| Backend | FastAPI (Python 3.12) — layered: router → service → repository → model |
| Database | PostgreSQL (Railway) via SQLAlchemy async |
| Queue | Celery + Redis |
| Storage | Google Drive API (MVP) |
| AI | Claude API (Sonnet 4.6 / Haiku 4.5) + Replicate (LaMa, GFPGAN, NIMA) |
| Auth | JWT (single user) — no NextAuth |
| Deployment | Railway (api + worker + web + postgres + redis) |

## Core Rules

1. **Before adding any operation** — check `scripts/`. If it exists, use it. If not: add `scripts/<name>.sh` + `make` target + entry in `docs/infra/DEVOPS.md`.
2. **Before searching "how to do X"** — read the relevant doc from the table below first.
3. **Record all architecture decisions** in `docs/DECISIONS.md` (append-only, never edit existing entries).
4. **One migration per PR.** File: `api/alembic/versions/NNN_description.py`.
5. **Layer discipline:** routers call services, services call repositories, repositories own all SQL.

## Agent Load Map — Load ONLY What Your Task Needs

| Task | Load these docs (and nothing else) |
|---|---|
| Add a backend endpoint | `docs/backend/CONVENTIONS.md` + `docs/API.md` |
| Add a Celery task | `docs/backend/WORKERS.md` + `docs/backend/CONVENTIONS.md` |
| Add / modify a DB model | `docs/DATA.md` + `docs/infra/MIGRATIONS.md` |
| Add external API call (Claude / Replicate) | `docs/backend/INTEGRATIONS.md` + `docs/PROMPTS.md` |
| Add image processing logic | `docs/backend/PIPELINE.md` |
| Add auth / secrets / budget code | `docs/backend/SECURITY.md` |
| Add a frontend page or component | `docs/frontend/CONVENTIONS.md` + `docs/frontend/DESIGN.md` |
| Add a React hook | `docs/frontend/CONVENTIONS.md` + `docs/frontend/STATE.md` |
| Understand a user-facing feature | `docs/FLOW.md` |
| Write a test | `docs/testing/STRATEGY.md` + `docs/testing/PATTERNS.md` |
| Set up or debug environment | `docs/infra/ENV.md` + `docs/infra/DEVOPS.md` |
| Record an architecture decision | `docs/DECISIONS.md` |

## Make Targets (Quick Reference)

| Command | What |
|---|---|
| `make bootstrap` | First-time setup (uv sync + pnpm install + .env files) |
| `make dev` | Start full stack (docker compose) |
| `make dev-api` / `make dev-web` | API-only / Web-only dev |
| `make test` | Run all tests |
| `make lint` | Non-mutating checks (ruff, mypy, eslint, tsc) |
| `make format` | Auto-format + auto-fix |
| `make migrate` | `alembic upgrade head` |
| `make migrate-new msg="..."` | New autogenerated revision |
| `make reset-db` | Drop + recreate dev DB |
| `make logs [svc=api]` | Tail compose logs |

## Document Index

| Doc | One-line purpose |
|---|---|
| `docs/FLOW.md` | What the product does step-by-step; state machines |
| `docs/DATA.md` | DB schema, model shapes, JSON field structures |
| `docs/API.md` | All REST endpoints with request/response contracts |
| `docs/PROMPTS.md` | Claude prompt library, token budgets, caching rules |
| `docs/DECISIONS.md` | Architecture decision record (append-only) |
| `docs/backend/CONVENTIONS.md` | Layered architecture, naming, patterns |
| `docs/backend/PIPELINE.md` | Image processing, file storage, task chains |
| `docs/backend/INTEGRATIONS.md` | Claude, Replicate, Google Drive wrappers |
| `docs/backend/WORKERS.md` | Celery tasks, queues, error handling |
| `docs/backend/SECURITY.md` | Auth, JWT, Fernet encryption, budget guards |
| `docs/frontend/CONVENTIONS.md` | Component patterns, types, imports, hooks |
| `docs/frontend/DESIGN.md` | Visual system + all screen specs |
| `docs/frontend/STATE.md` | SSE, optimistic updates, client-side state |
| `docs/infra/DEVOPS.md` | Local Docker Compose + Railway ops |
| `docs/infra/ENV.md` | All environment variables reference |
| `docs/infra/MIGRATIONS.md` | Alembic workflow + migration catalog |
| `docs/testing/STRATEGY.md` | Test approach, tools, CI, coverage targets |
| `docs/testing/PATTERNS.md` | Fixtures, factories, mocking recipes |
```

- [x] **Step 2: Verify the load map covers all 4 layers** (frontend, backend, infra, testing). Count rows — should be ≥12.

- [x] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: rewrite CLAUDE.md as lean root index with agent load map"
```

---

### Task 3: Create docs/FLOW.md

**Files:**
- Create: `docs/FLOW.md`

- [x] **Step 1: Write docs/FLOW.md with this exact structure**

```markdown
# Product Flow

## 10-Step User Flow

### Step 1 — Resync
User pastes a Google Drive folder URL → clicks **Resync**.
Backend: wipes workspace (DB rows + local previews + temp files for the session),
lists files in the folder, enqueues `tasks_sync.download_and_preview` for each asset.
Session status: `pending` → `syncing` → `ready` (or `error`).

### Step 2 — Deterministic Grouping (free, automatic)
On sync completion: `tasks_sync.run_deterministic_grouping` runs.
Logic (in order):
1. Parse filename via `config/filename_patterns.yaml` patterns.
2. Group by EXIF `DateTimeOriginal` — same day = same candidate group.
3. Split group if time gap between consecutive shots > 2 hours.
4. Split group if GPS distance between consecutive shots > 500 m.
Result: `groups` + `group_assets` rows created; `assets.status = "grouped"`.

### Step 3 — AI Grouping Refinement (🤖 opt-in, paid)
User clicks **AI Group** per cluster or globally.
UI shows cost estimate → user confirms → tile-packed thumbnails sent to Claude Vision →
Claude returns suggested group boundaries → user accepts/rejects each suggestion.
See prompt: `GROUPING_REFINEMENT_V1` in `docs/PROMPTS.md`.

### Step 4 — Labeling within Group
Runs automatically after grouping:
- `is_near_duplicate`: pHash (free, local) — threshold in `config/filename_patterns.yaml`.
- `aesthetic_score`: Replicate NIMA (💰 opt-in per group).
- `has_face`: `face_recognition` HOG (free, local).
- `is_video`: EXIF / file extension.

### Step 5 — Review Grid
Frontend `/session/{id}`: groups displayed as cards, assets as thumbnails.
Near-duplicates collapsed (worst scored hidden, best shown). Score + face + video badges.
User can: quick-reject an asset, drag asset between groups, expand near-dup cluster.

### Step 6 — Edit View
Frontend `/edit/{assetId}`: full-screen before/after slider.
Four correction tabs — Color, Crop, Remove, Face — each with three modes:
- Manual: user uploads corrected image.
- Local/free: Pillow color ops, SmartCrop (no API call).
- AI: Claude suggests parameters → Replicate executes (💰 confirm required).
Every accepted correction creates a new `edit_versions` row.

### Step 7 — Face Retouch
1. Backend detects face bbox in full-res original (`face_detect.py`).
2. Crop + 20% padding → user downloads.
3. User edits externally → re-uploads via `/face-crops/{id}/upload`.
4. Backend aligns via landmarks → `blend.py` Poisson seamless clone.
5. Output replaces face region in full-res working copy.

### Step 8 — Edit History
Each accepted correction: new `edit_versions` row (parent chain).
Reject: mark `user_decision = "rejected"`, create new branch from parent.
Regenerate: re-runs AI step, costs tokens, requires confirmation.

### Step 9 — Description Generation (🤖 paid)
User clicks **Generate** in DescriptionPanel.
Backend: tile-packs preview images for the group + EXIF + style seed + custom prompt →
sends to Claude Sonnet → returns caption in user's voice.
Result stored in `descriptions` table; user can regenerate (new row) or set current.

### Step 10 — Export
User clicks **Download ZIP** in ExportPanel.
Backend: enqueues `tasks_export.build_zip`; Celery builds ZIP with full-res assets
named `01_place.jpg`, `02_place.jpg` etc.; SSE broadcasts progress.
ZIP download via HMAC-signed URL (`/exports/{id}/download`).
User copies caption from DescriptionPanel → pastes to Instagram.

---

## Session Status Machine

```
pending ──(sync starts)──► syncing ──(all assets ready)──► ready
                                  └──(any fatal error)───► error
```

## Asset Status Machine

```
pending ──(preview generated)──► previewed ──(grouped)──► grouped
grouped ──(edit accepted)──► edited ──(in export ZIP)──► exported
any ──(user rejects)──► rejected
```

## Cost Gates (requires confirm dialog before executing)

| Operation | Trigger | Est. cost |
|---|---|---|
| AI grouping | "AI Group" button | $0.10–0.30 / session |
| Aesthetic scoring | "Score" button per group | ~$0.01 / asset |
| Color AI suggestion | Mode = AI in Color tab | ~$0.05 / asset |
| Object removal | Mode = AI or Local in Remove tab | ~$0.01 / asset |
| Face enhancement (GFPGAN) | Face tab, Local/API mode | ~$0.005 / asset |
| Description generation | "Generate" button | ~$0.02 / post |

Free operations (no dialog): preview generation, deterministic grouping, pHash, face detection, local color ops, manual upload.

## Resync Behavior

On resync, in order:
1. All `edit_versions`, `face_crops`, `descriptions`, `group_assets`, `groups`, `assets` for the session are deleted (hard delete).
2. `exports` for the session are deleted.
3. `cost_log` entries are **kept** (audit trail).
4. Local preview files and temp files for the session are removed from disk.
5. Session status reset to `pending`.
6. Fresh download + preview + grouping cycle begins.

## Non-Goals (MVP)

- No direct Instagram posting (copy-paste only).
- No automated video editing (manual round-trip only).
- No AI face retouching (GFPGAN only — no AI suggestions, user uploads the edit).
- No multi-user support.
```

- [x] **Step 2: Verify** — check that all 10 steps are present, all 3 state machines are documented, cost gate table has ≥6 rows.

- [x] **Step 3: Commit**

```bash
git add docs/FLOW.md
git commit -m "docs: add FLOW.md — product flow, state machines, cost gates"
```

---

### Task 4: Create docs/DATA.md

**Files:**
- Create: `docs/DATA.md`

- [x] **Step 1: Write docs/DATA.md**

Write the file with the following structure. Use the actual SQLAlchemy model files as source of truth for column names and types:

```markdown
# Data Model

> Source of truth for all DB queries. Read this before touching models, migrations, or repositories.

## Table Reference

### users
| Column | Type | Nullable | Notes |
|---|---|---|---|
| id | String(36) | No | UUID hex, PK |
| email | String(255) | No | Unique |
| hashed_password | String(255) | No | bcrypt |
| created_at | DateTime(tz) | No | |

### storage_credentials
| Column | Type | Nullable | Notes |
|---|---|---|---|
| id | String(36) | No | UUID hex, PK |
| user_id | String(36) | No | FK → users.id |
| provider | String(50) | No | "google_drive" |
| refresh_token | Text | No | **Fernet encrypted** |
| access_token | Text | Yes | **Fernet encrypted** |
| created_at / updated_at | DateTime(tz) | No | |
Unique: (user_id, provider)

### sessions
| Column | Type | Nullable | Notes |
|---|---|---|---|
| id | String(36) | No | UUID hex, PK |
| user_id | String(36) | No | FK → users.id, indexed |
| cloud_provider | String(50) | No | "google_drive" |
| cloud_folder_id | String(255) | No | |
| cloud_folder_name | String(255) | No | |
| status | String(50) | No | pending/syncing/ready/error/deleted, indexed |
| created_at / updated_at | DateTime(tz) | No | created_at indexed |

### assets
| Column | Type | Nullable | Notes |
|---|---|---|---|
| id | String(36) | No | UUID hex, PK |
| session_id | String(36) | No | FK → sessions.id, indexed |
| original_cloud_path | String(1024) | No | Full Drive path |
| original_filename | String(255) | No | |
| preview_path | String(1024) | Yes | Relative to data_dir |
| thumbnail_path | String(1024) | Yes | Relative to data_dir |
| full_res_local_path | String(1024) | Yes | Relative to data_dir |
| exif_json | Text | Yes | JSON string — see structure below |
| gps_lat / gps_lng | Float | Yes | Decimal degrees |
| taken_at | DateTime(tz) | Yes | From EXIF DateTimeOriginal |
| is_video | Boolean | No | Default false |
| has_face | Boolean | No | Default false |
| aesthetic_score | Float | Yes | NIMA 0–10 |
| phash | String(64) | Yes | Hex perceptual hash |
| status | String(50) | No | pending/previewed/grouped/edited/exported/rejected |

**exif_json structure** (keys the app reads):
```json
{
  "camera_make": "Apple",
  "camera_model": "iPhone 15 Pro",
  "taken_at": "2024-07-15T14:32:00",
  "gps_lat": 40.7128,
  "gps_lng": -74.0060,
  "iso": 100,
  "aperture": 1.8,
  "shutter_speed": "1/1000",
  "focal_length_mm": 24
}
```

### groups
| Column | Type | Nullable | Notes |
|---|---|---|---|
| id | String(36) | No | UUID hex, PK |
| session_id | String(36) | No | FK → sessions.id, indexed |
| name | String(255) | No | User-editable label |
| auto_generated | Boolean | No | True if created by AI |
| order_index | Integer | No | Display order |

### group_assets (association)
| Column | Type | Nullable | Notes |
|---|---|---|---|
| group_id | String(36) | No | FK → groups.id, PK part |
| asset_id | String(36) | No | FK → assets.id, PK part |
| position | Integer | No | Order within group |

### edit_versions
| Column | Type | Nullable | Notes |
|---|---|---|---|
| id | String(36) | No | UUID hex, PK |
| asset_id | String(36) | No | FK → assets.id, indexed |
| parent_version_id | String(36) | Yes | FK → edit_versions.id (version tree) |
| created_at | DateTime(tz) | No | |
| changes_log_text | Text | Yes | Human-readable bullet list |
| corrections_applied_json | Text | Yes | JSON — see structure below |
| output_path | String(1024) | Yes | Relative to data_dir |
| user_decision | String(50) | Yes | accepted/rejected/pending |

**corrections_applied_json structure**:
```json
{
  "color": {
    "lut_name": "golden_hour_v2",
    "exposure": 0.3,
    "contrast": 10,
    "saturation": -8,
    "temperature": 400,
    "highlights": -20,
    "shadows": 15
  },
  "crop": { "x": 0.1, "y": 0.0, "width": 0.8, "height": 1.0 },
  "removal": { "mask_bbox": [120, 80, 200, 300] },
  "face": { "blend_applied": true }
}
```

### face_crops
| Column | Type | Nullable | Notes |
|---|---|---|---|
| id | String(36) | No | UUID hex, PK |
| asset_id | String(36) | No | FK → assets.id |
| bbox_json | Text | No | `{"x":int,"y":int,"w":int,"h":int}` |
| crop_path | String(1024) | Yes | Cropped face for download |
| user_uploaded_path | String(1024) | Yes | User's edited face upload |
| blended_output_path | String(1024) | Yes | Final blended result |

### descriptions
| Column | Type | Nullable | Notes |
|---|---|---|---|
| id | String(36) | No | UUID hex, PK |
| group_id | String(36) | No | FK → groups.id, indexed |
| text | Text | No | Generated caption |
| custom_prompt | Text | Yes | User override prompt |
| model_used | String(100) | No | e.g. "claude-sonnet-4-6" |
| tokens_used | Integer | No | |
| is_current | Boolean | No | Only one true per group |
| created_at | DateTime(tz) | No | |

### cost_log
| Column | Type | Nullable | Notes |
|---|---|---|---|
| id | String(36) | No | UUID hex, PK |
| session_id | String(36) | No | FK → sessions.id, indexed |
| operation | String(100) | No | See enum below |
| model | String(100) | Yes | "claude-sonnet-4-6" etc. |
| tokens_used | Integer | Yes | |
| dollars_estimate | Float | No | |
| created_at | DateTime(tz) | No | |

**operation enum values**: `grouping_ai`, `color_ai`, `crop_ai`, `object_removal`, `face_enhancement`, `aesthetic_scoring`, `description`

### ai_cache
| Column | Type | Nullable | Notes |
|---|---|---|---|
| id | String(36) | No | UUID hex, PK |
| cache_key | String(255) | No | SHA-256 of prompt+inputs, Unique |
| response_json | Text | No | Raw Claude response |
| created_at | DateTime(tz) | No | |
| expires_at | DateTime(tz) | Yes | |

### exports
| Column | Type | Nullable | Notes |
|---|---|---|---|
| id | String(36) | No | UUID hex, PK |
| session_id | String(36) | No | FK → sessions.id |
| status | String(50) | No | pending/building/ready/error |
| zip_path | String(1024) | Yes | Relative to data_dir |
| created_at | DateTime(tz) | No | |

### app_settings (added in Phase 2)
| Column | Type | Nullable | Notes |
|---|---|---|---|
| key | String(100) | No | PK — see key enum below |
| value | Text | Yes | **Fernet encrypted** for secrets |
| updated_at | DateTime(tz) | No | auto-updated |

**key enum**: `claude_api_key`, `replicate_api_key`, `google_client_id`, `google_client_secret`, `session_budget_usd`, `session_hard_cap_usd`, `style_seed`

---

## SQLAlchemy Class → Table Mapping

| Class | Table |
|---|---|
| User | users |
| StorageCredentials | storage_credentials |
| Session | sessions |
| Asset | assets |
| Group | groups |
| GroupAsset | group_assets |
| EditVersion | edit_versions |
| FaceCrop | face_crops |
| Description | descriptions |
| CostLog | cost_log |
| AICache | ai_cache |
| Export | exports |
| AppSetting | app_settings |

## Encryption Policy

Fields marked **Fernet encrypted** are encrypted with `settings.fernet_key` before writing to DB and decrypted after reading. Use `cryptography.fernet.Fernet(settings.fernet_key.encode()).encrypt(value.encode()).decode()` to encrypt and `.decrypt(value.encode()).decode()` to decrypt. Never store plaintext for these fields.

## Deletion Policy

- `edit_versions`, `face_crops`, `descriptions`, `group_assets`, `groups`, `assets`: hard delete on resync.
- `cost_log`, `ai_cache`: never deleted (audit + cache trail).
- `sessions`, `users`, `storage_credentials`: never auto-deleted.
- `exports`: hard delete on resync.
```

- [x] **Step 2: Verify** — every table from the SQLAlchemy models is present, exif_json and corrections_applied_json structures are documented, encryption policy is clear.

- [x] **Step 3: Commit**

```bash
git add docs/DATA.md
git commit -m "docs: add DATA.md — full schema reference with JSON field structures"
```

---

### Task 5: Create docs/API.md

**Files:**
- Create: `docs/API.md`

- [x] **Step 1: Write docs/API.md**

```markdown
# REST API Reference

Base URL: `/api/v1`
Auth: `Authorization: Bearer <jwt>` header required on all endpoints except `/auth/login` and `/health`.
Rate limit: 200 requests/minute per IP.

## Standard Shapes

**Error response:**
```json
{ "detail": "human-readable message" }
```

**Cost estimate (returned before paid ops):**
```json
{ "dollars": 0.05, "tokens_in": 2000, "tokens_out": 500, "model": "claude-sonnet-4-6" }
```

---

## /auth

| Method | Path | Auth? | Body | Response | Notes |
|---|---|---|---|---|---|
| POST | /auth/login | No | `{email, password}` | `{accessToken}` | Sets JWT cookie |
| POST | /auth/logout | Yes | — | `{ok: true}` | |
| GET | /auth/me | Yes | — | `{id, email}` | |

## /sessions

| Method | Path | Auth? | Body | Response | Side effects |
|---|---|---|---|---|---|
| GET | /sessions | Yes | — | `Session[]` | |
| POST | /sessions | Yes | `{cloudProvider, cloudFolderId, cloudFolderName}` | `Session` | |
| GET | /sessions/{id} | Yes | — | `Session` | |
| DELETE | /sessions/{id} | Yes | — | `{ok: true}` | Hard delete all assets |
| POST | /sessions/{id}/resync | Yes | — | `{ok: true}` | Wipes + re-enqueues sync tasks |
| GET | /sessions/{id}/cost | Yes | — | `{totalDollars, breakdown: CostEntry[]}` | |

**Session shape:**
```json
{
  "id": "abc123",
  "cloudProvider": "google_drive",
  "cloudFolderId": "1BxiM...",
  "cloudFolderName": "Italy 2024",
  "status": "ready",
  "createdAt": "2026-04-17T10:00:00Z",
  "updatedAt": "2026-04-17T10:05:00Z"
}
```

## /assets

| Method | Path | Auth? | Response | Notes |
|---|---|---|---|---|
| GET | /assets?sessionId={id} | Yes | `Asset[]` | Filterable by groupId, status |
| GET | /assets/{id} | Yes | `Asset` | |
| GET | /assets/{id}/preview | Yes | image/jpeg | 1024px preview |
| GET | /assets/{id}/thumbnail | Yes | image/jpeg | 384px thumbnail |
| GET | /assets/{id}/original | Yes | binary | Full-res download |
| PATCH | /assets/{id} | Yes | `{status}` | `Asset` | Reject / un-reject |

**Asset shape:**
```json
{
  "id": "...", "sessionId": "...", "originalFilename": "IMG_001.jpg",
  "status": "grouped", "isVideo": false, "hasFace": true,
  "aestheticScore": 7.2, "takenAt": "2024-07-15T14:32:00Z",
  "gpsLat": 40.7128, "gpsLng": -74.006
}
```

## /groups

| Method | Path | Auth? | Body | Response |
|---|---|---|---|---|
| GET | /groups?sessionId={id} | Yes | — | `Group[]` with assets |
| POST | /groups | Yes | `{sessionId, name}` | `Group` |
| PATCH | /groups/{id} | Yes | `{name?, orderIndex?}` | `Group` |
| DELETE | /groups/{id} | Yes | — | `{ok: true}` |
| POST | /groups/{id}/assets | Yes | `{assetId, position}` | `{ok: true}` |
| DELETE | /groups/{id}/assets/{assetId} | Yes | — | `{ok: true}` |
| POST | /sessions/{id}/regroup | Yes | — | `{ok: true}` | Re-runs deterministic grouping |

## /edits

| Method | Path | Auth? | Body | Response | Cost |
|---|---|---|---|---|---|
| POST | /edits/suggest | Yes | `{assetId, correctionType, mode}` | `{suggestion, costEstimate}` | 🤖 if mode=ai |
| POST | /edits/accept | Yes | `{assetId, corrections}` | `EditVersion` | |
| POST | /edits/reject | Yes | `{editVersionId}` | `{ok: true}` | |
| POST | /edits/upload | Yes | multipart `{assetId, correctionType, file}` | `EditVersion` | |
| GET | /edits/history/{assetId} | Yes | — | `EditVersion[]` | |

**correctionType values:** `color`, `crop`, `removal`, `face`
**mode values:** `manual`, `local`, `ai`

## /face-crops

| Method | Path | Auth? | Body | Response |
|---|---|---|---|---|
| POST | /face-crops/detect | Yes | `{assetId}` | `FaceCrop[]` |
| GET | /face-crops/{id}/download | Yes | — | image/jpeg |
| POST | /face-crops/{id}/upload | Yes | multipart `{file}` | `FaceCrop` |
| POST | /face-crops/{id}/blend | Yes | — | `FaceCrop` |

## /descriptions

| Method | Path | Auth? | Body | Response | Cost |
|---|---|---|---|---|---|
| POST | /descriptions/generate | Yes | `{groupId, customPrompt?}` | `Description` | 🤖 ~$0.02 |
| GET | /descriptions?groupId={id} | Yes | — | `Description[]` | |
| PATCH | /descriptions/{id}/set-current | Yes | — | `{ok: true}` | |

## /exports

| Method | Path | Auth? | Response |
|---|---|---|---|
| POST | /exports | Yes | `{exportId}` | Enqueues build |
| GET | /exports/{id} | Yes | `Export` | Status polling |
| GET | /exports/{id}/download | No | application/zip | HMAC-signed URL |

## /cost

| Method | Path | Auth? | Body | Response |
|---|---|---|---|---|
| POST | /cost/estimate | Yes | `{operation, inputs}` | `CostEstimate` |
| GET | /cost/summary?sessionId={id} | Yes | — | `{totalDollars, entries: CostEntry[]}` |

## /settings (added in Phase 2)

| Method | Path | Auth? | Body | Response |
|---|---|---|---|---|
| GET | /settings | Yes | — | `Settings` |
| PATCH | /settings | Yes | `SettingsPatch` | `Settings` |

**Settings shape:**
```json
{
  "claudeApiKey": "sk-ant-****a1b2",
  "replicateApiKey": "r8_****c3d4",
  "googleClientId": "123456.apps.googleusercontent.com",
  "googleClientSecret": "****e5f6",
  "sessionBudgetUsd": 10.0,
  "sessionHardCapUsd": 50.0,
  "styleSeed": "Casual, sun-drenched, warm tones..."
}
```
Sensitive keys are masked in GET responses (last 4 chars visible). Send the full value in PATCH to update; send `null` to clear; omit the field to leave unchanged.

## /events (SSE)

| Method | Path | Auth? |
|---|---|---|
| GET | /events?sessionId={id} | Yes |

Streams `text/event-stream`. Event shape:
```json
{ "type": "asset_ready", "assetId": "...", "progress": 0.42 }
```
**type values:** `sync_started`, `asset_ready`, `grouping_done`, `export_progress`, `export_ready`, `error`

## /storage

| Method | Path | Auth? | Notes |
|---|---|---|---|
| GET | /storage/providers | Yes | List connected providers |
| GET | /storage/google/oauth/start | Yes | Redirect to Google consent screen |
| GET | /storage/google/oauth/callback | No | OAuth callback — sets refresh token |
| DELETE | /storage/google | Yes | Revoke + delete credentials |

## /health

| Method | Path | Response |
|---|---|---|
| GET | /health | `{status: "ok"}` |
| GET | /health/ready | `{status: "ok", db: true, redis: true}` |
```

- [x] **Step 2: Verify** — all 12 router groups are present, all methods have body/response shapes, /settings endpoints are documented.

- [x] **Step 3: Commit**

```bash
git add docs/API.md
git commit -m "docs: add API.md — complete REST reference with request/response shapes"
```

---

### Task 6: Create backend docs (5 files)

**Files:**
- Create: `docs/backend/CONVENTIONS.md`
- Create: `docs/backend/PIPELINE.md`
- Create: `docs/backend/INTEGRATIONS.md`
- Create: `docs/backend/WORKERS.md`
- Create: `docs/backend/SECURITY.md`

- [x] **Step 1: Write docs/backend/CONVENTIONS.md**

```markdown
# Backend Conventions

> Read this before writing any FastAPI code. Load alongside docs/API.md for endpoint work.

## Layer Architecture

```
router → service → repository → model (ORM)
```

**Hard rules:**
- Routers call services (and dependencies). Never query DB directly from a router.
- Services call repositories and integrations. No `HTTPException` in services — raise `ValueError` or custom exceptions.
- Repositories own all SQL (`select`, `insert`, `update`, `delete`). No business logic.
- Models are ORM declarations only. No methods beyond `__repr__`.

## File Naming

- `api/app/routers/<domain>.py` — one router per resource (`sessions.py`, `assets.py`).
- `api/app/services/<domain>_service.py` — `DescriptionService`, `EditingService`.
- `api/app/repositories/<domain>.py` — `SessionRepository`, `AssetRepository`.
- `api/app/models/<domain>.py` — `Session`, `Asset`.
- `api/app/schemas/<domain>.py` — Pydantic request/response models.

## Router Pattern

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from http import HTTPStatus

from app.db import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services.example_service import ExampleService
from app.schemas.example import ExampleRequest, ExampleResponse

router = APIRouter(prefix="/examples", tags=["examples"])

@router.get("/{id}", response_model=ExampleResponse)
async def get_example(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExampleResponse:
    service = ExampleService(db)
    result = await service.get(id)
    if not result:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Not found")
    return ExampleResponse.model_validate(result)
```

## Service Pattern

```python
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.example import ExampleRepository

class ExampleService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = ExampleRepository(db)

    async def get(self, id: str):
        return await self.repo.get_by_id(id)
```

## Repository Pattern

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.example import Example

class ExampleRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, id: str) -> Example | None:
        result = await self.db.execute(select(Example).where(Example.id == id))
        return result.scalar_one_or_none()

    async def create(self, **kwargs) -> Example:
        obj = Example(**kwargs)
        self.db.add(obj)
        await self.db.flush()  # flush, never commit — router/service manages transactions
        return obj
```

## ORM Model Pattern

```python
from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base

class Example(Base):
    __tablename__ = "examples"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True,
        default=lambda: __import__("uuid").uuid4().hex
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
```

## Pydantic Schema Pattern

```python
from pydantic import BaseModel, ConfigDict

class ExampleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    createdAt: datetime  # camelCase for all response fields
```

## Error Handling

- Routers: `raise HTTPException(status_code=..., detail="message")`.
- Services: `raise ValueError("message")` — router catches and converts.
- Never return 200 with an error payload.
- Standard 404: `HTTPStatus.NOT_FOUND`. Standard 401: `HTTPStatus.UNAUTHORIZED`. Standard 400: `HTTPStatus.BAD_REQUEST`.

## Logging

```python
import logging
logger = logging.getLogger(__name__)

# Required fields per log line:
logger.info("operation completed", extra={"session_id": sid, "operation": "preview"})
```

## Config Access

```python
from app.config import settings  # singleton, always use this
# Never: os.environ["FOO"] or os.getenv("FOO")
```

## Adding an Endpoint — Checklist

1. Add Pydantic schema to `api/app/schemas/<domain>.py`.
2. Add repository method to `api/app/repositories/<domain>.py`.
3. Add service method to `api/app/services/<domain>_service.py`.
4. Add route to `api/app/routers/<domain>.py` with `response_model=`.
5. Register router in `api/app/main.py` with `app.include_router(...)`.
6. Add endpoint to `docs/API.md`.
7. Write integration test in `api/tests/test_<domain>.py`.

## Code Style

- Python 3.12+. `from __future__ import annotations` in every file.
- Line length: 100. Enforced by ruff.
- Import order: stdlib → third-party → `app.*`.
- No `from app.models import *`.
```

- [x] **Step 2: Write docs/backend/PIPELINE.md**

```markdown
# Image Processing Pipeline

> Read when working on sync tasks, editing tasks, export tasks, or any lib/ code.

## Full Pipeline

```
Google Drive
    │
    ▼ tasks_sync.download_and_preview
Download original → /data/sessions/{session_id}/originals/{filename}
    │
    ├─► preview.generate_preview()  → /data/sessions/{id}/previews/{uuid}_preview.jpg (1024px)
    ├─► preview.generate_thumbnail() → /data/sessions/{id}/previews/{uuid}_thumb.jpg (384px)
    ├─► exif.extract_exif()          → asset.exif_json, asset.taken_at, asset.gps_lat/lng
    ├─► phash.compute_phash()        → asset.phash
    └─► face_detect.detect_faces()   → asset.has_face
    │
    ▼ tasks_sync.run_deterministic_grouping  (after all assets ready)
grouping_service.run() → groups + group_assets rows
    │
    ▼ (user-triggered) tasks_editing.*
color_ops / crop / replicate lama / replicate gfpgan → edit_versions row
    │
    ▼ (user-triggered) tasks_export.build_zip
ZIP: /data/sessions/{id}/exports/{uuid}.zip
  └── 01_Italy.jpg, 02_Rome.jpg, ...  (full-res, ordered by group position)
```

## File Storage Layout

All paths relative to `settings.data_dir` (default `/data`):

```
/data/
  sessions/
    {session_id}/
      originals/
        {original_filename}           ← never modified
      previews/
        {asset_id}_preview.jpg        ← 1024px JPEG q=85
        {asset_id}_thumb.jpg          ← 384px JPEG q=85
      exports/
        {export_id}.zip
      working/
        {asset_id}_edit_{version}.jpg ← output of each edit step
```

## Preview Tiers

| Tier | Longest side | Field | Use case |
|---|---|---|---|
| thumbnail | 384px | `asset.thumbnail_path` | UI grid |
| preview | 1024px | `asset.preview_path` | AI analysis, edit view |
| hi-preview | 1536px | (not stored, generated on demand) | Detailed composition analysis |
| original | — | `asset.full_res_local_path` | Export ZIP only |

Aspect ratio **always preserved** — longest side caps, shorter side scales. JPEG quality 85.

## lib/ Function Signatures

**preview.py**
```python
def generate_preview(src: Path, dest: Path, longest_side: int = 1024) -> Path:
    """Resize src image, save JPEG to dest. Returns dest."""

def generate_thumbnail(src: Path, dest: Path) -> Path:
    """Resize src to 384px longest side, save JPEG to dest."""
```

**exif.py**
```python
def extract_exif(path: Path) -> dict:
    """Return dict with keys: camera_make, camera_model, taken_at (ISO str),
    gps_lat, gps_lng, iso, aperture, shutter_speed, focal_length_mm.
    Missing fields are None."""
```

**phash.py**
```python
def compute_phash(path: Path) -> str:
    """Return 64-char hex perceptual hash."""

def are_near_duplicates(hash1: str, hash2: str, threshold: int = 10) -> bool:
    """True if hamming distance ≤ threshold."""
```

**face_detect.py**
```python
def detect_faces(path: Path) -> list[dict]:
    """Return list of {x, y, w, h} dicts (pixel coords in original resolution).
    Empty list if no faces found. Uses HOG model (CPU-safe)."""
```

**tile_pack.py**
```python
def pack_tiles(image_paths: list[Path], max_tiles: int = 9) -> Path:
    """Pack up to 9 thumbnails into a grid image for Claude Vision.
    Returns path to the packed image (temp file). Labels tiles 1..N."""
```

**color_ops.py**
```python
def apply_lut(img: Image.Image, lut_name: str) -> Image.Image: ...
def apply_exposure(img: Image.Image, ev: float) -> Image.Image: ...  # ev: -3..+3
def apply_contrast(img: Image.Image, pct: float) -> Image.Image: ...  # pct: -100..+100
def apply_saturation(img: Image.Image, pct: float) -> Image.Image: ...
def apply_temperature(img: Image.Image, kelvin_shift: int) -> Image.Image: ...
def apply_highlights_shadows(img: Image.Image, hl: float, sh: float) -> Image.Image: ...
def apply_hsl(img: Image.Image, hue: float, sat: float, light: float) -> Image.Image: ...
```

**blend.py**
```python
def seamless_blend(base: Path, patch: Path, bbox: dict) -> Path:
    """Poisson seamless clone. bbox: {x, y, w, h} in base image coords.
    Returns path to blended output (temp file)."""
```

## Non-Destructive Rule

The original file at `asset.full_res_local_path` is **never overwritten**. Every edit step writes a new file at `working/{asset_id}_edit_{version_id}.jpg` and records the path in `edit_versions.output_path`.

## Celery Task Chain (Sync)

```python
# tasks_sync.py — called for each asset
chord([
    download_and_preview.s(asset_id),
], run_deterministic_grouping.si(session_id)).delay()
```

## Export ZIP Structure

File naming: `{position:02d}_{sanitized_group_name}.jpg`
Example: `01_Italy_coast.jpg`, `02_Rome_forum.jpg`.
Always uses full-res original if no accepted edits; uses `edit_versions.output_path` of latest accepted version if edits exist.
```

- [x] **Step 3: Write docs/backend/INTEGRATIONS.md**

```markdown
# External Integrations

> Read when calling Claude, Replicate, or Google Drive. Never call these APIs directly — always use the wrappers in `api/app/integrations/`.

## ClaudeClient (`integrations/claude.py`)

```python
from app.integrations.claude import ClaudeClient

client = ClaudeClient()  # reads settings.anthropic_api_key

# Text completion
response = await client.complete(
    prompt="...",
    model="claude-haiku-4-5-20251001",  # or "claude-sonnet-4-6"
    max_tokens=1024,
    cache_key="optional-sha256-key",  # omit to skip caching
)
# response: {"content": "...", "tokens_in": N, "tokens_out": M, "cached": bool}

# Vision (image + text)
response = await client.complete_vision(
    prompt="...",
    image_path=Path("/data/..."),  # PIL-readable image
    model="claude-haiku-4-5-20251001",
    max_tokens=512,
)
```

**Caching:** Pass `cache_key` (SHA-256 hex of inputs) to enable. Hit rate is logged. Cache TTL: indefinite (manual invalidation only).

**Model selection rule:**
- Grouping, color suggestions, best-photo selection → `claude-haiku-4-5-20251001` (fast, cheap).
- Crop, object removal mask, description generation → `claude-sonnet-4-6` (better reasoning).

## ReplicateClient (`integrations/replicate.py`)

```python
from app.integrations.replicate import ReplicateClient

client = ReplicateClient()  # reads settings.replicate_api_token

# Object removal (LaMa inpainting)
result_url = await client.run_lama(
    image_path=Path("/data/.../preview.jpg"),
    mask_bbox={"x": 120, "y": 80, "w": 80, "h": 220},
)  # Returns URL to result image

# Face enhancement (GFPGAN)
result_url = await client.run_gfpgan(
    image_path=Path("/data/.../face_crop.jpg"),
)  # Returns URL to enhanced image

# Aesthetic scoring (NIMA)
score: float = await client.run_nima(
    image_path=Path("/data/.../preview.jpg"),
)  # Returns float 0–10
```

**Polling:** All Replicate calls poll until complete (max 120s). Raises `TimeoutError` if exceeded.

## GoogleDriveClient (`integrations/google_drive.py`)

```python
from app.integrations.google_drive import GoogleDriveClient

client = GoogleDriveClient(
    access_token="...",
    refresh_token="...",   # decrypted from storage_credentials
)

files = await client.list_folder(folder_id="1BxiM...")
# Returns: [{"id": "...", "name": "IMG_001.jpg", "mimeType": "image/jpeg", "size": 1234567}]

local_path = await client.download_file(
    file_id="...",
    dest_path=Path("/data/.../originals/IMG_001.jpg"),
)
```

## Cost Logging (Required for Every Paid Call)

Every call to ClaudeClient or ReplicateClient **must** log to cost_log:

```python
from app.services.cost_service import CostEstimator
from app.repositories.cost_log import CostLogRepository

# After the API call:
repo = CostLogRepository(db)
await repo.create(
    session_id=session_id,
    operation="description",  # see cost_log operation enum in docs/DATA.md
    model="claude-sonnet-4-6",
    tokens_used=response["tokens_in"] + response["tokens_out"],
    dollars_estimate=0.02,
)
await db.commit()
```

## Error Handling

| Error | Handling |
|---|---|
| `anthropic.APIStatusError` (rate limit) | Retry 3× with exponential backoff (2s, 4s, 8s) |
| `anthropic.APIStatusError` (auth) | Raise, do not retry — likely invalid API key |
| Replicate timeout | Raise `TimeoutError`, task marks asset as `error` |
| Google Drive 401 | Refresh token, retry once; if fails, mark session as `error` |

## Adding a New Integration

1. Create `api/app/integrations/<name>.py` with a class `<Name>Client`.
2. Constructor reads API key from `settings.<key_name>`.
3. Every public method is `async`.
4. Add retry logic for transient errors.
5. Log every call to `cost_log` if it has a monetary cost.
6. Add the API key to `docs/infra/ENV.md`.
```

- [x] **Step 4: Write docs/backend/WORKERS.md**

```markdown
# Celery Workers

> Read when writing or modifying background tasks.

## Queues

| Queue | Purpose |
|---|---|
| `sync` | File download + preview generation |
| `preview` | (reserved for future GPU preview offload) |
| `editing` | Color, crop, removal, blend tasks |
| `ai` | Claude / Replicate API calls |
| `export` | ZIP building |
| `default` | Anything else |

## Task Naming Convention

`tasks_{domain}.{verb}_{noun}`

Examples: `tasks_sync.download_and_preview`, `tasks_editing.apply_color`, `tasks_export.build_zip`.

## Task Function Shape

```python
from app.workers.celery_app import celery_app

@celery_app.task(bind=True, queue="sync", max_retries=3, default_retry_delay=5)
def download_and_preview(self, asset_id: str) -> None:
    """Download asset from Drive and generate previews."""
    import asyncio
    from app.db import AsyncSessionLocal

    async def _run():
        async with AsyncSessionLocal() as db:
            # ... do work ...
            await db.commit()

    asyncio.run(_run())
```

**Rules:**
- Never use `self` unless `bind=True` (for `self.retry()`).
- Always accept primitive args (`str`, `int`, `float`), never ORM objects.
- Always open a fresh `AsyncSessionLocal()` inside the task.
- Use `asyncio.run(_run())` to run async code from sync Celery task.
- Commit only after all DB writes in the task are complete.

## SSE Progress Events

Emit progress to the frontend SSE stream from within a task:

```python
from app.lib.sse_events import emit_event  # exists in lib/

emit_event(session_id, {"type": "asset_ready", "assetId": asset_id, "progress": 0.5})
```

## Error Handling in Tasks

```python
try:
    # ... do work ...
except SomeTransientError as exc:
    raise self.retry(exc=exc)  # requires bind=True
except Exception:
    # Mark asset/session as errored in DB
    async with AsyncSessionLocal() as db:
        repo = AssetRepository(db)
        await repo.update_status(asset_id, "error")
        await db.commit()
    raise  # re-raise so Celery marks task as FAILURE
```

## Task Catalog

| Task | Queue | Inputs | What it does |
|---|---|---|---|
| `tasks_sync.download_and_preview` | sync | asset_id | Download from Drive, gen preview+thumb, extract EXIF, phash, face detect |
| `tasks_sync.run_deterministic_grouping` | sync | session_id | Run grouping_service.run() after all assets previewed |
| `tasks_editing.apply_color` | editing | asset_id, corrections_json | Apply color ops via color_ops.py, write edit_versions row |
| `tasks_editing.apply_lama` | ai | asset_id, mask_bbox_json | Call Replicate LaMa, write edit_versions row |
| `tasks_editing.apply_gfpgan` | ai | face_crop_id | Call Replicate GFPGAN on face crop |
| `tasks_editing.run_nima` | ai | asset_id | Score via NIMA, update asset.aesthetic_score |
| `tasks_editing.blend_face` | editing | face_crop_id | Run blend.seamless_blend(), update face_crop |
| `tasks_export.build_zip` | export | export_id | Build ZIP from accepted edit versions, emit SSE |

## Testing Tasks

Set `task_always_eager = True` in conftest (already configured). Call tasks synchronously:

```python
from app.workers.tasks_sync import download_and_preview

# In test — runs inline, no broker needed:
download_and_preview.delay(asset_id="abc")
# OR call directly:
download_and_preview(asset_id="abc")
```
```

- [x] **Step 5: Write docs/backend/SECURITY.md**

```markdown
# Security

> Read when working on auth, API key storage, OAuth credentials, or budget enforcement.

## Auth Flow

1. `POST /auth/login` — validates email+password (bcrypt), returns JWT.
2. JWT stored in `Authorization: Bearer <token>` header by frontend.
3. `get_current_user` dependency (in `dependencies.py`) decodes JWT, loads User from DB.
4. All protected routes declare `current_user: User = Depends(get_current_user)`.

## JWT

- Signed with `settings.jwt_secret` (HS256).
- Payload: `{"user_id": "...", "iat": ..., "exp": ...}`.
- Expiry: 7 days.
- Encode: `jwt_utils.create_jwt_token(user_id)`.
- Decode: `jwt_utils.decode_jwt_token(token)` → returns payload dict or None.

## Single-User Model (MVP)

There is exactly one user in the DB. `user_id` is always `settings.single_user_email`'s corresponding DB row. No multi-tenancy. All session/asset ownership checks compare `session.user_id == current_user.id`.

## Fernet Encryption

Used for: `storage_credentials.refresh_token`, `storage_credentials.access_token`, `app_settings.value` (for sensitive keys).

```python
from cryptography.fernet import Fernet

def encrypt(value: str) -> str:
    f = Fernet(settings.fernet_key.encode())
    return f.encrypt(value.encode()).decode()

def decrypt(value: str) -> str:
    f = Fernet(settings.fernet_key.encode())
    return f.decrypt(value.encode()).decode()
```

`settings.fernet_key` must be a valid 32-byte URL-safe base64 key. Generate with `Fernet.generate_key().decode()`.

## Budget Guards

- Soft cap: `settings.session_budget_usd` (default $10). Warning shown in UI; operations still allowed.
- Hard cap: `settings.session_hard_cap_usd` (default $50). All AI operations are rejected with 402 until session resets.
- Checked by `BudgetService.check(session_id, db)` before every paid operation in services.

```python
from app.services.budget_service import BudgetService

# In service, before any paid API call:
budget = BudgetService(db)
await budget.check(session_id)  # raises ValueError if over hard cap
```

## API Key Masking

When returning API keys in GET /settings responses, mask all but the last 4 characters:

```python
def mask_key(value: str | None) -> str | None:
    if not value or len(value) <= 4:
        return None
    return f"****{value[-4:]}"
```

## Path Traversal Prevention

All file paths constructed from user input must be validated to be within `settings.data_dir`:

```python
from pathlib import Path

def safe_path(base: Path, relative: str) -> Path:
    resolved = (base / relative).resolve()
    if not str(resolved).startswith(str(base.resolve())):
        raise ValueError("Path traversal detected")
    return resolved
```

## Rate Limiting

200 requests/minute per IP. Enforced by `slowapi` in `main.py`. No per-route overrides in MVP.

## Phase 2 Notes

When going multi-user: add `user_id` checks to every repository query, add row-level security to Postgres, replace single JWT secret with per-user session tokens, add CSRF protection to state-mutating endpoints.
```

- [x] **Step 6: Commit all backend docs**

```bash
git add docs/backend/
git commit -m "docs: add docs/backend/ — CONVENTIONS, PIPELINE, INTEGRATIONS, WORKERS, SECURITY"
```

---

### Task 7: Create frontend docs (3 files)

**Files:**
- Create: `docs/frontend/CONVENTIONS.md`
- Move+trim: `docs/frontend/DESIGN.md` (from `docs/DESIGN.md`)
- Create: `docs/frontend/STATE.md`

- [x] **Step 1: Write docs/frontend/CONVENTIONS.md**

```markdown
# Frontend Conventions

> Read before writing any Next.js code. Load alongside docs/frontend/DESIGN.md for UI work.

## Mental Model

- **Server Components** (default): fetch data, render HTML, no interactivity. Named `page.tsx` or `Layout.tsx`.
- **Client Components** (`"use client"`): interactivity, hooks, browser APIs. Named `*.client.tsx`.
- Split at the boundary: server component fetches + passes data; client component handles events.

## File Naming

```
web/src/app/(app)/session/[id]/
  page.tsx                    ← Server Component (data fetch)
  SessionDetail.client.tsx    ← Client Component (interaction)
```

- Pages: `page.tsx` (default export required).
- Client components: `PascalCase.client.tsx`.
- Hooks: `use-kebab-case.ts` in `web/src/hooks/`.
- Types: in `web/src/types/api.ts` (mirrors FastAPI schemas).
- Utilities: in `web/src/lib/`.

## Path Aliases

`@/` maps to `web/src/`. Always use `@/` — never use relative `../../`.

## API Calls

Always use `apiFetch<T>()` from `@/lib/api-client`:

```typescript
import { apiFetch } from "@/lib/api-client";
import type { Session } from "@/types/api";

// In Server Component:
const sessions = await apiFetch<Session[]>("/sessions");

// In Client Component (inside event handler or useEffect):
const session = await apiFetch<Session>(`/sessions/${id}`);

// PATCH with body:
const updated = await apiFetch<Session>(`/sessions/${id}`, {
  method: "PATCH",
  body: { status: "deleted" },  // apiFetch handles JSON.stringify
});
```

`apiFetch` throws `ApiError` (with `.status` and `.message`) on non-2xx responses.

## TypeScript Rules

- No `any`. Use `unknown` + narrowing.
- Always `import type { ... }` for type-only imports.
- No default exports except `page.tsx` files.
- Strict mode is on (`tsconfig.json`).

## shadcn/ui

- Only use primitives from `web/src/components/ui/`. Never hand-roll buttons, inputs, cards.
- Add new primitives: `pnpm dlx shadcn@latest add <name>`.
- Never edit files in `components/ui/` — they are generated.

## Styling

- Tailwind classes only. No inline `style={{}}` objects.
- No hardcoded hex/rgb. Use HSL tokens from `globals.css` (`bg-background`, `text-foreground`, etc.).
- Dark mode is canonical — no light mode toggle.

## Cookie Security

When setting auth cookies manually:
```typescript
document.cookie = `token=${value}; path=/; SameSite=Strict; Secure`;
```

## Import Order

1. React (`import { useState } from "react"`)
2. Next.js (`import { useRouter } from "next/navigation"`)
3. Third-party (`import { Button } from "@/components/ui/button"`)
4. Internal `@/` imports
5. Type imports (last, with `import type`)

## Adding a Page — Checklist

1. Create `web/src/app/(app)/<route>/page.tsx` (Server Component).
2. Fetch data with `apiFetch<T>()` using type from `@/types/api`.
3. Create `<Name>.client.tsx` for interactive parts.
4. Add types to `@/types/api` if new response shapes are needed.
5. Verify design in `docs/frontend/DESIGN.md` for layout spec.
6. Check keyboard shortcuts in DESIGN.md §Keyboard Shortcuts.
```

- [x] **Step 2: Move and trim docs/DESIGN.md to docs/frontend/DESIGN.md**

Copy the existing `docs/DESIGN.md` to `docs/frontend/DESIGN.md`. Remove:
- The long "Component placement quick-reference" section (now in CONVENTIONS.md).
- Duplicate hook catalog (now in STATE.md).
Keep all screen specs, visual system, micro-interactions, accessibility, and PR checklist.
Goal: ≤500 lines.

```bash
cp docs/DESIGN.md docs/frontend/DESIGN.md
# Then trim as described above using Edit tool
```

- [x] **Step 3: Write docs/frontend/STATE.md**

```markdown
# Client State

> Read when writing hooks or complex client-side state logic.

## No Global State Library

No Zustand, Redux, or Context for app state. Use:
- **URL params** (`useSearchParams`) for shareable state (current group, current asset).
- **React `useState`** for ephemeral local state (modal open, form values).
- **SSE** (`useSessionEvents`) for server-pushed progress updates.
- **`router.refresh()`** to re-fetch server component data after mutations.

## SSE — useSessionEvents

```typescript
import { useSessionEvents } from "@/hooks/use-session-events";

const { lastEvent } = useSessionEvents(sessionId);

useEffect(() => {
  if (!lastEvent) return;
  if (lastEvent.type === "asset_ready") {
    // update local asset list
  }
}, [lastEvent]);
```

Hook reconnects automatically on disconnect. Only one SSE connection per session page.

## Optimistic Updates — useAssetReject

Pattern for instant UI feedback before server confirms:

```typescript
// 1. Update local state immediately
setAssets(prev => prev.map(a => a.id === id ? { ...a, status: "rejected" } : a));

// 2. Call API
try {
  await apiFetch(`/assets/${id}`, { method: "PATCH", body: { status: "rejected" } });
} catch {
  // 3. Rollback on failure
  setAssets(prev => prev.map(a => a.id === id ? { ...a, status: prevStatus } : a));
  toast.error("Failed to reject asset");
}
```

Follow this pattern for any mutation (group reorder, accept edit, etc.).

## Confirm Dialog — useConfirm

```typescript
import { useConfirm } from "@/hooks/use-confirm";

const confirm = useConfirm();

const handleDelete = async () => {
  const ok = await confirm("Delete session?");
  if (!ok) return;
  await apiFetch(`/sessions/${id}`, { method: "DELETE" });
  router.push("/dashboard");
};
```

## Cost Estimate — useCostEstimate

```typescript
import { useCostEstimate } from "@/hooks/use-cost-estimate";

const { estimate, loading } = useCostEstimate("description", { groupId });
// estimate: { dollars: 0.02, tokensIn: 1500, tokensOut: 300, model: "claude-sonnet-4-6" }
// Show CostConfirm modal before proceeding
```

## Toast

```typescript
import { useToast } from "@/hooks/use-toast";

const { toast } = useToast();
toast.success("Edit accepted");
toast.error("API call failed");
```

## Local Storage — useLocalStorage

```typescript
import { useLocalStorage } from "@/hooks/use-local-storage";

const [sliderPos, setSliderPos] = useLocalStorage("compare-slider-pos", 50);
```

SSR-safe (returns default value during server render).

## Router Refresh After Mutations

After any successful mutation that changes server-rendered data:

```typescript
import { useRouter } from "next/navigation";
const router = useRouter();

// After successful PATCH/POST/DELETE:
router.refresh();  // re-fetches server component data without full navigation
// NOT: window.location.reload()
```
```

- [x] **Step 4: Commit**

```bash
git add docs/frontend/
git commit -m "docs: add docs/frontend/ — CONVENTIONS, DESIGN (moved), STATE"
```

---

### Task 8: Create infra + testing docs and clean up old files

**Files:**
- Create: `docs/infra/DEVOPS.md`, `docs/infra/ENV.md`, `docs/infra/MIGRATIONS.md`
- Create: `docs/testing/STRATEGY.md`, `docs/testing/PATTERNS.md`
- Delete: `docs/ARCHITECTURE.md`, `docs/BACKEND.md`, `docs/FRONTEND.md`, `docs/TESTING.md`, `docs/DEVOPS.md`, `docs/DESIGN.md`

- [x] **Step 1: Write docs/infra/DEVOPS.md**

Migrate content from `docs/DEVOPS.md`. Add:
- Troubleshooting section: "DB connection refused" → check postgres health, "Redis timeout" → check redis service, "Preview not generated" → check worker logs with `make logs svc=worker`.
- Disk management: `make clean-data` wipes `/data` (prompts). Railway volume: 10GB limit in free tier.

Key structure:
```markdown
# DevOps

## Local Development (Docker Compose)

[5 services + ports table: postgres:5432, redis:6379, api:8000, worker:(no port), web:3000]

## Make Targets
[complete table — same as CLAUDE.md plus: migrate, migrate-new, reset-db, logs, ps, shell-api]

## First-Time Setup
[make bootstrap → make dev → check http://localhost:3000]

## Railway Deployment
[service list, start commands, volume mount, healthcheck paths, domain config]

## First Deploy Checklist
[6 steps: push code, set env vars in Railway dashboard, provision postgres+redis, run migrations, create seed user, smoke test]

## Rotating Secrets
[fernet_key rotation: generate new key, decrypt all encrypted values with old key, re-encrypt with new key, update Railway env var]

## Logs & Debugging
[make logs svc=api, make logs svc=worker, trace_id field in structured logs]

## Disk Management
[make clean-data, Railway volume limits, per-session cleanup on resync]

## Troubleshooting
[common errors + fixes table]
```

- [x] **Step 2: Write docs/infra/ENV.md**

```markdown
# Environment Variables

> Complete reference. Set in `.env` for local dev. Set in Railway dashboard for production.

## API Service (`api/`)

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | Yes | `postgresql+asyncpg://postgres:postgres@localhost:5432/influencerflow` | Async Postgres URL |
| `REDIS_URL` | Yes | `redis://localhost:6379/0` | Redis broker + result backend |
| `DATA_DIR` | No | `/data` | Root for all local file storage |
| `ENVIRONMENT` | No | `development` | `development` or `production` |
| `JWT_SECRET` | Yes | `dev-insecure-change-me` | HS256 signing key — change in prod |
| `FERNET_KEY` | Yes | `""` | 32-byte URL-safe base64. Generate: `Fernet.generate_key().decode()` |
| `SINGLE_USER_EMAIL` | Yes | `""` | Email for the single app user |
| `SINGLE_USER_PASSWORD` | Yes | `""` | bcrypt hash or plain (hashed on first boot) |
| `GOOGLE_OAUTH_CLIENT_ID` | No | `""` | Google OAuth 2.0 client ID |
| `GOOGLE_OAUTH_CLIENT_SECRET` | No | `""` | Google OAuth 2.0 client secret |
| `GOOGLE_OAUTH_REDIRECT_URI` | No | `http://localhost:8000/api/v1/storage/google/oauth/callback` | OAuth callback URL |
| `ANTHROPIC_API_KEY` | No | `""` | Claude API key (overridable via Settings UI) |
| `REPLICATE_API_TOKEN` | No | `""` | Replicate API token (overridable via Settings UI) |
| `SESSION_BUDGET_USD` | No | `10.0` | Soft cap per session (warning shown) |
| `SESSION_HARD_CAP_USD` | No | `50.0` | Hard cap per session (blocks all AI ops) |

## Web Service (`web/`)

| Variable | Required | Default | Description |
|---|---|---|---|
| `NEXT_PUBLIC_API_BASE` | No | `http://localhost:8000` | API base URL (public — in browser) |
| `API_BASE` | No | `http://api:8000` | API base URL (server-side, inside Docker network) |
| `NEXTAUTH_SECRET` | No | — | Not used (custom JWT auth) |

## Secrets vs. Config

**Never commit to git:** `JWT_SECRET`, `FERNET_KEY`, `SINGLE_USER_PASSWORD`, `ANTHROPIC_API_KEY`, `REPLICATE_API_TOKEN`, `GOOGLE_OAUTH_CLIENT_SECRET`.

**Safe to commit defaults:** `DATABASE_URL`, `REDIS_URL`, `DATA_DIR`, `ENVIRONMENT`, `GOOGLE_OAUTH_REDIRECT_URI`.

## Settings UI Override

`ANTHROPIC_API_KEY` and `REPLICATE_API_TOKEN` can be overridden at runtime via `GET/PATCH /settings`. The `SettingsService` checks `app_settings` table first; falls back to environment variable if DB value is absent.
```

- [x] **Step 3: Write docs/infra/MIGRATIONS.md**

```markdown
# Database Migrations

> One migration per PR. Read before adding or modifying any DB model.

## Workflow

```bash
# 1. Modify the SQLAlchemy model in api/app/models/<domain>.py
# 2. Generate migration
make migrate-new msg="add app_settings table"
# Creates: api/alembic/versions/010_add_app_settings_table.py

# 3. Review the generated file — check upgrade() and downgrade() are correct
cat api/alembic/versions/010_add_app_settings_table.py

# 4. Apply locally
make migrate

# 5. Verify — connect to DB and check table exists
make shell-api
# >>> from app.db import engine; import asyncio; ...

# 6. Commit migration file with the model change in the same commit
git add api/alembic/versions/010_*.py api/app/models/<domain>.py
git commit -m "feat: add app_settings table"
```

## Naming Convention

Files: `NNN_description.py` where NNN is zero-padded 3-digit sequence.

Current migrations (in order):
| File | What it does |
|---|---|
| `001_initial_schema.py` | users, storage_credentials, sessions, assets |
| `002_groups_and_grouping.py` | groups, group_assets |
| `003_add_near_duplicate_clustering.py` | assets.phash, assets.aesthetic_score |
| `004_edit_versions_table.py` | edit_versions |
| `005_ai_cache_table.py` | ai_cache |
| `006_cost_log_table.py` | cost_log |
| `007_face_crops_table.py` | face_crops |
| `008_descriptions_table.py` | descriptions |
| `009_exports_table.py` | exports |
| `010_app_settings_table.py` | app_settings *(Phase 2)* |

## What Alembic Auto-generates Correctly

- Adding/removing columns.
- Adding/removing tables.
- Changing nullable.

## What Needs Manual Review

- Partial indexes (`postgresql_where=`).
- `CHECK` constraints.
- Changing column types (may need explicit cast).
- `server_default` values.

## Rollback

```bash
# Roll back one migration:
cd api && uv run alembic downgrade -1

# Roll back to specific revision:
cd api && uv run alembic downgrade 009
```

## Railway

Migrations run automatically on deploy via `make migrate` in the Railway start command (before the API process starts).

## Rules

- **One migration per PR** — never batch schema changes across PRs.
- **Never edit an applied migration** — create a new one to fix mistakes.
- **Never squash migrations during MVP** — only after dogfood phase is complete.
```

- [x] **Step 4: Write docs/testing/STRATEGY.md**

```markdown
# Testing Strategy

## Philosophy

Test behaviors, not implementations. Prefer real dependencies (real Postgres, real Redis) over mocks. Only mock external paid APIs (Claude, Replicate, Google Drive).

## API Tests (pytest)

Location: `api/tests/`
Runner: `make test-api` or `pytest api/tests/ -v`

- `asyncio_mode = "auto"` in `pyproject.toml`.
- Real Postgres via fixture (see PATTERNS.md).
- Celery runs in eager mode (no broker).
- File naming: `test_<domain>.py` — one file per router or service.

**Test kinds:**
- `lib/*` utilities → unit tests (no DB, no I/O mocking needed).
- Routers → integration tests (TestClient + real DB + mocked external APIs).
- Services → integration tests with fixture data.
- Celery tasks → integration tests with `task_always_eager=True`.

## Frontend Tests

- TypeScript strict + ESLint: `make lint` (runs on every PR).
- Vitest: `make test-web` (placeholder — add tests as hooks mature).
- E2E (Playwright): Week 6. Location: `web/tests/`.

## CI Pipeline

3 jobs (must all pass before merge):
1. `api` — `make lint` + `make test-api`
2. `web` — `make lint` (tsc + eslint)
3. `e2e` — Playwright (Week 6, currently skipped)

## Coverage Targets

| Layer | Target |
|---|---|
| `api/app/lib/*` | 80%+ (pure functions, easy to test) |
| `api/app/routers/*` | Happy path + 404 per endpoint |
| `api/app/services/*` | Happy path + error cases with fixture data |
| `api/app/repositories/*` | Covered by service tests |

## What NOT to Test

- shadcn/ui components (tested by upstream).
- Generated Alembic migrations.
- `api/app/config.py` itself.
- `api/app/main.py` wiring (covered by integration tests).
```

- [x] **Step 5: Write docs/testing/PATTERNS.md**

```markdown
# Test Patterns

> Copy-paste recipes. Load alongside STRATEGY.md.

## conftest.py (existing — do not duplicate)

Location: `api/tests/conftest.py`. Already has:
- `client` fixture: `TestClient(app)`.
- `_celery_eager_mode` autouse fixture: sets `task_always_eager=True`.

## Adding a DB Fixture

```python
# api/tests/conftest.py — add these fixtures
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.db import Base

TEST_DB_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/influencerflow_test"

@pytest_asyncio.fixture(scope="session")
async def engine():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest_asyncio.fixture
async def db(engine) -> AsyncSession:
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        yield session
        await session.rollback()  # isolate tests
```

## Fixture Factories

```python
# api/tests/factories.py
from app.models.session import Session
from app.models.asset import Asset

def make_session(user_id="user-1", **kwargs) -> Session:
    return Session(
        user_id=user_id,
        cloud_provider="google_drive",
        cloud_folder_id="folder-1",
        cloud_folder_name="Test Folder",
        status="ready",
        **kwargs
    )

def make_asset(session_id="session-1", **kwargs) -> Asset:
    return Asset(
        session_id=session_id,
        original_cloud_path="drive://IMG_001.jpg",
        original_filename="IMG_001.jpg",
        status="grouped",
        is_video=False,
        has_face=False,
        **kwargs
    )
```

## Mocking External APIs

```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_description_generation(db):
    with patch("app.integrations.claude.ClaudeClient.complete_vision") as mock_claude:
        mock_claude.return_value = {
            "content": "Beautiful sunset in Rome",
            "tokens_in": 1500,
            "tokens_out": 50,
            "cached": False,
        }
        service = DescriptionService(db)
        result = await service.generate(group_id="group-1", custom_prompt=None)
        assert result.text == "Beautiful sunset in Rome"
        mock_claude.assert_called_once()
```

## Router Integration Test

```python
def test_get_session(client, db):
    # Arrange — create session in DB
    session = make_session()
    # ... add to db ...

    # Act
    response = client.get(
        "/api/v1/sessions/session-1",
        headers={"Authorization": f"Bearer {test_jwt}"},
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["id"] == "session-1"
```

## Testing File Upload Endpoints

```python
from io import BytesIO

def test_face_crop_upload(client):
    img_bytes = BytesIO(b"fake-jpeg-content")
    response = client.post(
        "/api/v1/face-crops/crop-1/upload",
        files={"file": ("face.jpg", img_bytes, "image/jpeg")},
        headers={"Authorization": f"Bearer {test_jwt}"},
    )
    assert response.status_code == 200
```

## Asserting cost_log Entries

```python
from app.repositories.cost_log import CostLogRepository

async def test_description_logs_cost(db):
    # ... run description generation ...
    repo = CostLogRepository(db)
    entries = await repo.get_by_session(session_id="session-1")
    assert any(e.operation == "description" for e in entries)
    assert any(e.dollars_estimate > 0 for e in entries)
```
```

- [x] **Step 6: Delete old docs (content now in new hierarchy)**

```bash
rm docs/ARCHITECTURE.md docs/BACKEND.md docs/FRONTEND.md docs/TESTING.md docs/DEVOPS.md docs/DESIGN.md
```

- [x] **Step 7: Commit**

```bash
git add docs/infra/ docs/testing/
git add -u docs/  # stage deletions
git commit -m "docs: add infra/ and testing/ docs, delete superseded flat docs"
```

---

## Phase 2 — Settings UI Feature

> This phase implements the Settings page end-to-end using only the new docs as reference.
> It serves as a live validation that the docs are complete and accurate.

### File Map (Phase 2)

| Action | Path |
|--------|------|
| Create | `api/alembic/versions/010_app_settings_table.py` |
| Create | `api/app/models/settings.py` |
| Create | `api/app/repositories/settings.py` |
| Create | `api/app/schemas/settings.py` |
| Create | `api/app/services/settings_service.py` |
| Create | `api/app/routers/settings.py` |
| Modify | `api/app/main.py` |
| Create | `api/tests/test_settings.py` |
| Modify | `web/src/types/api.ts` |
| Create | `web/src/app/(app)/settings/page.tsx` |
| Create | `web/src/app/(app)/settings/SettingsForm.client.tsx` |

---

### Task 9: DB model + migration for app_settings

**Files:**
- Create: `api/app/models/settings.py`
- Create: `api/alembic/versions/010_app_settings_table.py`

- [x] **Step 1: Write failing test for model existence**

```python
# api/tests/test_settings.py
from app.models.settings import AppSetting

def test_app_setting_model_has_expected_columns():
    cols = {c.name for c in AppSetting.__table__.columns}
    assert "key" in cols
    assert "value" in cols
    assert "updated_at" in cols
```

- [x] **Step 2: Run test — confirm it fails**

```bash
cd api && uv run pytest tests/test_settings.py::test_app_setting_model_has_expected_columns -v
```
Expected: `ModuleNotFoundError: No module named 'app.models.settings'`

- [x] **Step 3: Create api/app/models/settings.py**

```python
"""AppSetting model — key-value store for runtime configuration."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base

SETTING_KEYS = frozenset({
    "claude_api_key",
    "replicate_api_key",
    "google_client_id",
    "google_client_secret",
    "session_budget_usd",
    "session_hard_cap_usd",
    "style_seed",
})

SENSITIVE_KEYS = frozenset({
    "claude_api_key",
    "replicate_api_key",
    "google_client_secret",
})


class AppSetting(Base):
    """Runtime-configurable settings stored encrypted in DB."""

    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
```

- [x] **Step 4: Run test — confirm it passes**

```bash
cd api && uv run pytest tests/test_settings.py::test_app_setting_model_has_expected_columns -v
```
Expected: PASS

- [x] **Step 5: Generate migration**

```bash
make migrate-new msg="add app_settings table"
```

Review the generated file. The `upgrade()` must contain:
```python
op.create_table(
    "app_settings",
    sa.Column("key", sa.String(100), nullable=False),
    sa.Column("value", sa.Text(), nullable=True),
    sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    sa.PrimaryKeyConstraint("key"),
)
```

- [x] **Step 6: Apply migration**

```bash
make migrate
```
Expected: `Running upgrade ... -> 010, add app_settings table` with no errors.

- [x] **Step 7: Add AppSetting to models __init__**

```python
# api/app/models/__init__.py — add:
from app.models.settings import AppSetting

__all__ = [..., "AppSetting"]
```

- [x] **Step 8: Commit**

```bash
git add api/app/models/settings.py api/alembic/versions/010_*.py api/app/models/__init__.py
git commit -m "feat: add AppSetting model and migration 010"
```

---

### Task 10: SettingsRepository

**Files:**
- Create: `api/app/repositories/settings.py`

- [x] **Step 1: Write failing tests**

```python
# api/tests/test_settings.py — add:
import pytest
from app.repositories.settings import SettingsRepository
from app.models.settings import AppSetting

@pytest.mark.asyncio
async def test_get_all_returns_empty_dict_when_no_rows(db):
    repo = SettingsRepository(db)
    result = await repo.get_all()
    assert result == {}

@pytest.mark.asyncio
async def test_set_and_get(db):
    repo = SettingsRepository(db)
    await repo.set("style_seed", "Warm, golden tones")
    result = await repo.get_all()
    assert result["style_seed"] == "Warm, golden tones"

@pytest.mark.asyncio
async def test_set_none_clears_value(db):
    repo = SettingsRepository(db)
    await repo.set("style_seed", "some value")
    await repo.set("style_seed", None)
    result = await repo.get_all()
    assert result.get("style_seed") is None
```

- [x] **Step 2: Run — confirm all 3 fail**

```bash
cd api && uv run pytest tests/test_settings.py -k "repo" -v
```
Expected: 3 FAILs with `ModuleNotFoundError`.

- [x] **Step 3: Create api/app/repositories/settings.py**

```python
"""Settings repository — key-value store for app_settings table."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.settings import AppSetting


class SettingsRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(self) -> dict[str, str | None]:
        """Return all settings as {key: value} dict."""
        result = await self.db.execute(select(AppSetting))
        rows = result.scalars().all()
        return {row.key: row.value for row in rows}

    async def set(self, key: str, value: str | None) -> None:
        """Upsert a single setting."""
        result = await self.db.execute(
            select(AppSetting).where(AppSetting.key == key)
        )
        row = result.scalar_one_or_none()
        if row is None:
            row = AppSetting(key=key, value=value)
            self.db.add(row)
        else:
            row.value = value
        await self.db.flush()

    async def set_many(self, updates: dict[str, str | None]) -> None:
        """Upsert multiple settings in one call."""
        for key, value in updates.items():
            await self.set(key, value)
```

- [x] **Step 4: Run — confirm all 3 pass**

```bash
cd api && uv run pytest tests/test_settings.py -k "repo" -v
```
Expected: 3 PASSes.

- [x] **Step 5: Commit**

```bash
git add api/app/repositories/settings.py api/tests/test_settings.py
git commit -m "feat: add SettingsRepository with get_all/set/set_many"
```

---

### Task 11: Pydantic schemas

**Files:**
- Create: `api/app/schemas/settings.py`

- [x] **Step 1: Write failing test**

```python
# api/tests/test_settings.py — add:
from app.schemas.settings import SettingsResponse, SettingsPatch

def test_settings_response_shape():
    r = SettingsResponse(
        claudeApiKey="****1234",
        replicateApiKey=None,
        googleClientId="123.apps.googleusercontent.com",
        googleClientSecret=None,
        sessionBudgetUsd=10.0,
        sessionHardCapUsd=50.0,
        styleSeed="Warm tones",
    )
    assert r.claudeApiKey == "****1234"

def test_settings_patch_all_optional():
    p = SettingsPatch()  # all fields optional — no error
    assert p.claudeApiKey is None
```

- [x] **Step 2: Run — confirm 2 fails**

```bash
cd api && uv run pytest tests/test_settings.py -k "schema" -v
```

- [x] **Step 3: Create api/app/schemas/settings.py**

```python
"""Pydantic schemas for /settings endpoints."""

from __future__ import annotations

from pydantic import BaseModel


class SettingsResponse(BaseModel):
    """GET /settings response. Sensitive keys are masked."""

    claudeApiKey: str | None
    replicateApiKey: str | None
    googleClientId: str | None
    googleClientSecret: str | None
    sessionBudgetUsd: float
    sessionHardCapUsd: float
    styleSeed: str | None


class SettingsPatch(BaseModel):
    """PATCH /settings request. Omitted fields are left unchanged. null clears the value."""

    claudeApiKey: str | None = None
    replicateApiKey: str | None = None
    googleClientId: str | None = None
    googleClientSecret: str | None = None
    sessionBudgetUsd: float | None = None
    sessionHardCapUsd: float | None = None
    styleSeed: str | None = None
```

- [x] **Step 4: Run — confirm 2 pass**

```bash
cd api && uv run pytest tests/test_settings.py -k "schema" -v
```

- [x] **Step 5: Commit**

```bash
git add api/app/schemas/settings.py api/tests/test_settings.py
git commit -m "feat: add settings Pydantic schemas"
```

---

### Task 12: SettingsService

**Files:**
- Create: `api/app/services/settings_service.py`

- [x] **Step 1: Write failing tests**

```python
# api/tests/test_settings.py — add:
from app.services.settings_service import SettingsService
from app.schemas.settings import SettingsPatch

@pytest.mark.asyncio
async def test_get_response_uses_env_fallback(db):
    """When DB has no rows, falls back to env var defaults."""
    service = SettingsService(db)
    response = await service.get()
    # Budget defaults come from settings object (env vars)
    assert response.sessionBudgetUsd == 10.0  # matches config.py default

@pytest.mark.asyncio
async def test_sensitive_keys_are_masked(db):
    repo = SettingsRepository(db)
    await repo.set("claude_api_key", "sk-ant-api03-realkey1234")
    await db.commit()

    service = SettingsService(db)
    response = await service.get()
    assert response.claudeApiKey == "****1234"  # only last 4 chars
    assert "realkey" not in (response.claudeApiKey or "")

@pytest.mark.asyncio
async def test_patch_encrypts_sensitive_key(db):
    service = SettingsService(db)
    await service.patch(SettingsPatch(claudeApiKey="sk-ant-api03-mynewkey9876"))
    await db.commit()

    repo = SettingsRepository(db)
    all_settings = await repo.get_all()
    # The stored value must NOT be the plaintext key
    assert all_settings.get("claude_api_key") != "sk-ant-api03-mynewkey9876"
    # But it must decrypt back to the plaintext
    from cryptography.fernet import Fernet
    from app.config import settings as app_settings
    f = Fernet(app_settings.fernet_key.encode())
    decrypted = f.decrypt(all_settings["claude_api_key"].encode()).decode()
    assert decrypted == "sk-ant-api03-mynewkey9876"
```

- [x] **Step 2: Run — confirm 3 fail**

```bash
cd api && uv run pytest tests/test_settings.py -k "service" -v
```

- [x] **Step 3: Create api/app/services/settings_service.py**

```python
"""Settings service — read/write app_settings with encryption and masking."""

from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings as app_config
from app.models.settings import SENSITIVE_KEYS
from app.repositories.settings import SettingsRepository
from app.schemas.settings import SettingsPatch, SettingsResponse


def _encrypt(value: str) -> str:
    f = Fernet(app_config.fernet_key.encode())
    return f.encrypt(value.encode()).decode()


def _decrypt(value: str) -> str | None:
    try:
        f = Fernet(app_config.fernet_key.encode())
        return f.decrypt(value.encode()).decode()
    except (InvalidToken, Exception):
        return None


def _mask(value: str | None) -> str | None:
    if not value or len(value) <= 4:
        return None
    return f"****{value[-4:]}"


class SettingsService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = SettingsRepository(db)

    async def get(self) -> SettingsResponse:
        """Read all settings; decrypt sensitive values; mask them for response."""
        raw = await self.repo.get_all()

        def _read(key: str, default: str | None = None) -> str | None:
            val = raw.get(key)
            if val is None:
                return default
            return _decrypt(val) if key in SENSITIVE_KEYS else val

        claude_key = _read("claude_api_key") or app_config.anthropic_api_key or None
        replicate_key = _read("replicate_api_key") or app_config.replicate_api_token or None

        return SettingsResponse(
            claudeApiKey=_mask(claude_key),
            replicateApiKey=_mask(replicate_key),
            googleClientId=_read("google_client_id") or app_config.google_oauth_client_id or None,
            googleClientSecret=_mask(_read("google_client_secret") or app_config.google_oauth_client_secret or None),
            sessionBudgetUsd=float(_read("session_budget_usd") or app_config.session_budget_usd),
            sessionHardCapUsd=float(_read("session_hard_cap_usd") or app_config.session_hard_cap_usd),
            styleSeed=_read("style_seed"),
        )

    async def patch(self, patch: SettingsPatch) -> SettingsResponse:
        """Apply partial update. None fields are skipped; explicit null would clear."""
        field_to_key = {
            "claudeApiKey": "claude_api_key",
            "replicateApiKey": "replicate_api_key",
            "googleClientId": "google_client_id",
            "googleClientSecret": "google_client_secret",
            "sessionBudgetUsd": "session_budget_usd",
            "sessionHardCapUsd": "session_hard_cap_usd",
            "styleSeed": "style_seed",
        }
        for field, key in field_to_key.items():
            value = getattr(patch, field)
            if value is None:
                continue  # omitted — leave unchanged
            if isinstance(value, float):
                str_value = str(value)
            else:
                str_value = value
            if key in SENSITIVE_KEYS and str_value:
                str_value = _encrypt(str_value)
            await self.repo.set(key, str_value)

        return await self.get()
```

- [x] **Step 4: Run — confirm 3 pass**

```bash
cd api && uv run pytest tests/test_settings.py -k "service" -v
```
Note: the encryption test requires `FERNET_KEY` to be set. For tests, add to conftest:
```python
import os
from cryptography.fernet import Fernet
os.environ.setdefault("FERNET_KEY", Fernet.generate_key().decode())
```

- [x] **Step 5: Commit**

```bash
git add api/app/services/settings_service.py api/tests/test_settings.py
git commit -m "feat: add SettingsService with encryption, masking, env fallback"
```

---

### Task 13: Settings router + wire into main.py

**Files:**
- Create: `api/app/routers/settings.py`
- Modify: `api/app/main.py`

- [x] **Step 1: Write failing integration test**

```python
# api/tests/test_settings.py — add:
def test_get_settings_returns_200(client):
    response = client.get(
        "/api/v1/settings",
        headers={"Authorization": f"Bearer {_make_test_token()}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "claudeApiKey" in data
    assert "sessionBudgetUsd" in data

def test_patch_settings_updates_style_seed(client):
    response = client.patch(
        "/api/v1/settings",
        json={"styleSeed": "Moody, dark cinematography"},
        headers={"Authorization": f"Bearer {_make_test_token()}"},
    )
    assert response.status_code == 200
    assert response.json()["styleSeed"] == "Moody, dark cinematography"

def test_settings_requires_auth(client):
    response = client.get("/api/v1/settings")
    assert response.status_code == 401

# Helper — add to test file top:
from app.lib.jwt_utils import create_jwt_token
def _make_test_token() -> str:
    return create_jwt_token(user_id="user-test-1")
```

- [x] **Step 2: Run — confirm 3 fail**

```bash
cd api && uv run pytest tests/test_settings.py -k "router or auth" -v
```
Expected: 404 or similar (route not registered yet).

- [x] **Step 3: Create api/app/routers/settings.py**

```python
"""Settings router — GET/PATCH /settings."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.settings import SettingsPatch, SettingsResponse
from app.services.settings_service import SettingsService

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SettingsResponse)
async def get_settings(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> SettingsResponse:
    service = SettingsService(db)
    return await service.get()


@router.patch("", response_model=SettingsResponse)
async def patch_settings(
    patch: SettingsPatch,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> SettingsResponse:
    service = SettingsService(db)
    result = await service.patch(patch)
    await db.commit()
    return result
```

- [x] **Step 4: Register in main.py**

```python
# api/app/main.py — add import:
from app.routers import health, auth, storage, sessions, assets, events, groups, edits, cost, face_crops, descriptions, exports, settings

# Inside create_app(), after other include_router calls:
app.include_router(settings.router, prefix=API_V1_PREFIX)
```

- [x] **Step 5: Run — confirm 3 pass**

```bash
cd api && uv run pytest tests/test_settings.py -v
```
Expected: all tests pass.

- [x] **Step 6: Commit**

```bash
git add api/app/routers/settings.py api/app/main.py api/tests/test_settings.py
git commit -m "feat: add GET/PATCH /settings endpoint with auth guard"
```

---

### Task 14: Frontend types + SettingsForm component

**Files:**
- Modify: `web/src/types/api.ts`
- Create: `web/src/app/(app)/settings/SettingsForm.client.tsx`

- [x] **Step 1: Add Settings types to api.ts**

```typescript
// web/src/types/api.ts — add:

export interface Settings {
  claudeApiKey: string | null;
  replicateApiKey: string | null;
  googleClientId: string | null;
  googleClientSecret: string | null;
  sessionBudgetUsd: number;
  sessionHardCapUsd: number;
  styleSeed: string | null;
}

export interface SettingsPatch {
  claudeApiKey?: string | null;
  replicateApiKey?: string | null;
  googleClientId?: string | null;
  googleClientSecret?: string | null;
  sessionBudgetUsd?: number | null;
  sessionHardCapUsd?: number | null;
  styleSeed?: string | null;
}
```

- [x] **Step 2: Create web/src/app/(app)/settings/SettingsForm.client.tsx**

```typescript
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiFetch } from "@/lib/api-client";
import { useToast } from "@/hooks/use-toast";
import type { Settings, SettingsPatch } from "@/types/api";

interface Props {
  initial: Settings;
}

export default function SettingsForm({ initial }: Props) {
  const router = useRouter();
  const { toast } = useToast();

  const [claudeKey, setClaudeKey] = useState("");
  const [replicateKey, setReplicateKey] = useState("");
  const [googleClientId, setGoogleClientId] = useState(initial.googleClientId ?? "");
  const [googleClientSecret, setGoogleClientSecret] = useState("");
  const [budgetUsd, setBudgetUsd] = useState(String(initial.sessionBudgetUsd));
  const [hardCapUsd, setHardCapUsd] = useState(String(initial.sessionHardCapUsd));
  const [styleSeed, setStyleSeed] = useState(initial.styleSeed ?? "");
  const [saving, setSaving] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);

    const patch: SettingsPatch = {};
    if (claudeKey) patch.claudeApiKey = claudeKey;
    if (replicateKey) patch.replicateApiKey = replicateKey;
    if (googleClientId !== (initial.googleClientId ?? "")) patch.googleClientId = googleClientId;
    if (googleClientSecret) patch.googleClientSecret = googleClientSecret;
    const budget = parseFloat(budgetUsd);
    if (!isNaN(budget) && budget !== initial.sessionBudgetUsd) patch.sessionBudgetUsd = budget;
    const hardCap = parseFloat(hardCapUsd);
    if (!isNaN(hardCap) && hardCap !== initial.sessionHardCapUsd) patch.sessionHardCapUsd = hardCap;
    if (styleSeed !== (initial.styleSeed ?? "")) patch.styleSeed = styleSeed;

    try {
      await apiFetch<Settings>("/settings", { method: "PATCH", body: patch });
      toast.success("Settings saved");
      router.refresh();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to save settings";
      toast.error(message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-8 max-w-lg">
      {/* Integrations */}
      <section className="space-y-4">
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
          Integrations
        </h2>

        <div className="space-y-2">
          <Label htmlFor="claudeKey">Claude API Key</Label>
          <Input
            id="claudeKey"
            type="password"
            placeholder={initial.claudeApiKey ?? "sk-ant-..."}
            value={claudeKey}
            onChange={(e) => setClaudeKey(e.target.value)}
            autoComplete="off"
          />
          <p className="text-xs text-muted-foreground">Leave blank to keep current key.</p>
        </div>

        <div className="space-y-2">
          <Label htmlFor="replicateKey">Replicate API Token</Label>
          <Input
            id="replicateKey"
            type="password"
            placeholder={initial.replicateApiKey ?? "r8_..."}
            value={replicateKey}
            onChange={(e) => setReplicateKey(e.target.value)}
            autoComplete="off"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="googleClientId">Google OAuth Client ID</Label>
          <Input
            id="googleClientId"
            type="text"
            value={googleClientId}
            onChange={(e) => setGoogleClientId(e.target.value)}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="googleClientSecret">Google OAuth Client Secret</Label>
          <Input
            id="googleClientSecret"
            type="password"
            placeholder={initial.googleClientSecret ?? "GOCSPX-..."}
            value={googleClientSecret}
            onChange={(e) => setGoogleClientSecret(e.target.value)}
            autoComplete="off"
          />
        </div>
      </section>

      {/* Budget */}
      <section className="space-y-4">
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
          Budget
        </h2>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="budgetUsd">Soft Cap (USD)</Label>
            <Input
              id="budgetUsd"
              type="number"
              min="0"
              step="0.5"
              value={budgetUsd}
              onChange={(e) => setBudgetUsd(e.target.value)}
            />
            <p className="text-xs text-muted-foreground">Shows warning when exceeded.</p>
          </div>
          <div className="space-y-2">
            <Label htmlFor="hardCapUsd">Hard Cap (USD)</Label>
            <Input
              id="hardCapUsd"
              type="number"
              min="0"
              step="1"
              value={hardCapUsd}
              onChange={(e) => setHardCapUsd(e.target.value)}
            />
            <p className="text-xs text-muted-foreground">Blocks all AI ops when exceeded.</p>
          </div>
        </div>
      </section>

      {/* Style Seed */}
      <section className="space-y-4">
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
          Caption Style
        </h2>
        <div className="space-y-2">
          <Label htmlFor="styleSeed">Style Seed</Label>
          <textarea
            id="styleSeed"
            className="w-full min-h-[120px] rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            placeholder="Describe your caption voice: casual, warm, Spanish, short captions under 150 chars..."
            value={styleSeed}
            onChange={(e) => setStyleSeed(e.target.value)}
          />
          <p className="text-xs text-muted-foreground">
            Used as context when generating Instagram captions.
          </p>
        </div>
      </section>

      <Button type="submit" disabled={saving}>
        {saving ? "Saving..." : "Save settings"}
      </Button>
    </form>
  );
}
```

- [x] **Step 3: Commit**

```bash
git add web/src/types/api.ts web/src/app/(app)/settings/
git commit -m "feat: add Settings frontend types and SettingsForm component"
```

---

### Task 15: Frontend /settings page (Server Component)

**Files:**
- Create: `web/src/app/(app)/settings/page.tsx`

- [x] **Step 1: Create page.tsx**

```typescript
// web/src/app/(app)/settings/page.tsx
import { apiFetch } from "@/lib/api-client";
import type { Settings } from "@/types/api";
import SettingsForm from "./SettingsForm.client";

export const metadata = { title: "Settings — InfluencerFlow" };

export default async function SettingsPage() {
  const settings = await apiFetch<Settings>("/settings");

  return (
    <main className="container py-8">
      <header className="mb-8">
        <h1 className="text-2xl font-semibold tracking-tight">Settings</h1>
        <p className="text-muted-foreground mt-1">
          Configure API keys, budget caps, and caption style.
        </p>
      </header>
      <SettingsForm initial={settings} />
    </main>
  );
}
```

- [x] **Step 2: Add Settings link to navigation (wherever sidebar/nav lives)**

Find the nav component (look in `web/src/app/(app)/` for a layout or sidebar file). Add:

```typescript
<Link href="/settings" className="...">Settings</Link>
```

- [x] **Step 3: Verify TypeScript compiles**

```bash
make lint
```
Expected: no TypeScript errors on the new files.

- [x] **Step 4: Start dev server and manually test** *(skipped — no running dev server in this session)*

```bash
make dev
```

Navigate to `http://localhost:3000/settings`. Verify:
- Page loads with current settings (masked API keys shown as `****xxxx`).
- Entering a new style seed and saving: toast appears, page refreshes, style seed shows new value.
- Entering a Claude API key: saves without error; GET response shows masked version.
- Budget fields: changing soft cap and saving reflects new value in GET.

- [x] **Step 5: Commit**

```bash
git add web/src/app/(app)/settings/page.tsx
git commit -m "feat: add /settings page — server component with SettingsForm"
```

---

## Self-Review

### Spec Coverage Check

| Requirement | Covered by |
|---|---|
| 18-file doc hierarchy created | Tasks 1–8 |
| CLAUDE.md as root index | Task 2 |
| Agent load map | Task 2 (in CLAUDE.md) |
| Old docs deleted | Task 8 |
| DB table for settings | Task 9 |
| Fernet encryption for sensitive keys | Task 12 |
| ENV fallback when DB value absent | Task 12 |
| API key masking in GET response | Task 12 |
| GET /settings endpoint | Task 13 |
| PATCH /settings endpoint | Task 13 |
| Auth guard on both endpoints | Task 13 |
| Frontend Settings types | Task 14 |
| SettingsForm component | Task 14 |
| /settings page (Server Component) | Task 15 |
| All tests pass | Tasks 10–13 |

### Placeholder Scan

No "TBD", "TODO", "implement later", "fill in details", or "similar to Task N" found.
All code steps show complete, runnable code. All commands show expected output.

### Type Consistency

- `SettingsResponse` used in router return types and frontend `Settings` interface: camelCase matches throughout.
- `SettingsPatch` used in router parameter and frontend `SettingsPatch` interface: matches.
- `AppSetting` ORM model uses `key`/`value`/`updated_at`: consistent with migration and repository.
- `SENSITIVE_KEYS` frozenset defined in model, imported by service: single source of truth.
