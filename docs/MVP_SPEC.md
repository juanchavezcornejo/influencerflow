# MVP_SPEC.md — InfluencerFlow

> **Project:** InfluencerFlow
> **Document:** MVP Build Specification
> **Status:** Draft v0.1
> **Last updated:** 2026-04-16
> **Scope:** 6-week solo build. Personal use. Dogfood-ready at end of W6.
> **Companion docs:** [CLAUDE.md](../CLAUDE.md), [ARCHITECTURE.md](./ARCHITECTURE.md), [PROMPTS.md](./PROMPTS.md)

---

## Table of Contents

1. [MVP Definition & Success Criteria](#1-mvp-definition--success-criteria)
2. [Global Conventions](#2-global-conventions)
3. [Week 0 — Setup & Scaffolding](#3-week-0--setup--scaffolding)
4. [Week 1 — Auth, Sync, Previews](#4-week-1--auth-sync-previews)
5. [Week 2 — Grouping & Review UI](#5-week-2--grouping--review-ui)
6. [Week 3 — Edit View & Color Corrections](#6-week-3--edit-view--color-corrections)
7. [Week 4 — Object Removal & Face Retouch](#7-week-4--object-removal--face-retouch)
8. [Week 5 — Descriptions, Export, Cost Tracking](#8-week-5--descriptions-export-cost-tracking)
9. [Week 6 — Polish & Dogfood](#9-week-6--polish--dogfood)
10. [Out of Scope for MVP](#10-out-of-scope-for-mvp)
11. [Risk Register](#11-risk-register)
12. [Dogfood Checklist](#12-dogfood-checklist)

---

## 1. MVP Definition & Success Criteria

**Definition of MVP:** Juan can take a Google Drive folder with 100 photos + a few videos from a real trip, run it through InfluencerFlow end-to-end, and export a ZIP + captions that he would actually post to Instagram.

### Must-have (all required)
- [ ] Login with a single email/password.
- [ ] Connect Google Drive via OAuth.
- [ ] Resync: wipe + download + generate previews for up to 200 files.
- [ ] Deterministic grouping by EXIF date + GPS + time gap.
- [ ] Review grid with near-duplicate collapsing.
- [ ] Edit view with before/after slider.
- [ ] Local color presets (3 proposals).
- [ ] Object removal via Replicate LaMa.
- [ ] Face crop → manual edit → upload → Poisson blend.
- [ ] Description generation via Claude.
- [ ] Per-group ZIP export.
- [ ] Cost badge + confirmation modal on every paid op.
- [ ] Cost log visible per session.

### Nice-to-have (if time remains)
- [ ] AI grouping refinement.
- [ ] Replicate NIMA aesthetic scoring.
- [ ] Mega integration.
- [ ] Edit history UI.
- [ ] Style learning from past captions.

### Explicitly deferred to V1+
See [§10 Out of Scope](#10-out-of-scope-for-mvp).

### Success Criteria (end of W6)
1. Juan can go from "200 photos in Drive" to "ZIP + caption ready to paste into Instagram" in under 30 minutes of active time.
2. Total AI + Replicate cost for such a session stays under **$5**.
3. Zero data loss: originals are never modified, and Resync only wipes app-managed temp storage.
4. All paid ops show cost estimate before executing.

---

## 2. Global Conventions

### 2.1 Branching & PRs
- `main` = deployable.
- Feature branches: `w{N}-{ticket-slug}`, e.g. `w1-gdrive-oauth`.
- One PR per ticket. PR description links to the ticket.

### 2.2 Ticket Format
Every ticket in this doc follows:

```
### TCKT-{CODE} — {Title}
Scope: {backend | frontend | full-stack}
Estimate: {S=2-4h | M=4-8h | L=8-16h}
Depends on: {TCKT-...}
Acceptance criteria:
  - [ ] ...
```

### 2.3 Tech Conventions
- **Python:** `ruff` (lint + format), `mypy --strict` where practical, `pytest`.
- **TypeScript:** `eslint` + `prettier`, `tsc --noEmit` in CI.
- **Commit messages:** Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`).
- **DB migrations:** Alembic, one per PR that touches schema.
- **Feature flags:** Simple env-based toggles for AI features (default OFF in dev).

### 2.4 Definition of Done (applies to every ticket)
- Code merged to `main`.
- Tests passing in CI.
- If UI: smoke-tested manually in Railway preview env.
- If cost-related: a row appears in `cost_log` with correct values.
- Docs updated if behavior diverges from `ARCHITECTURE.md`.

### 2.5 Estimates Legend
- **S (Small):** 2–4 hours focused work.
- **M (Medium):** 4–8 hours.
- **L (Large):** 8–16 hours. Consider splitting.

---

## 3. Week 0 — Setup & Scaffolding

> **Goal:** Empty but runnable skeleton. Nothing works yet end-to-end, but `docker-compose up` boots everything and `/health` returns 200.

### TCKT-W0-001 — Repository scaffolding
Scope: full-stack
Estimate: M
Depends on: —
Acceptance criteria:
- [ ] Monorepo created with `web/` and `api/` directories per `ARCHITECTURE.md §3`.
- [ ] `README.md` with dev setup instructions.
- [ ] `.gitignore`, `.editorconfig`, `LICENSE` (MIT or proprietary, Juan decides).
- [ ] `docker-compose.yml` with `postgres`, `redis`, `api`, `worker`, `web` services.
- [ ] `docker-compose up` boots cleanly.

### TCKT-W0-002 — FastAPI scaffold
Scope: backend
Estimate: M
Depends on: W0-001
Acceptance criteria:
- [ ] `pyproject.toml` with dependencies pinned.
- [ ] `app/main.py` exposes `/api/v1/health` and `/api/v1/health/ready`.
- [ ] SQLAlchemy async engine wired to `DATABASE_URL`.
- [ ] Alembic initialized (`alembic init alembic`).
- [ ] Pydantic Settings class reads env.
- [ ] `ruff` + `mypy` + `pytest` configured and green.

### TCKT-W0-003 — Celery scaffold
Scope: backend
Estimate: S
Depends on: W0-002
Acceptance criteria:
- [ ] `app/workers/celery_app.py` with Redis broker.
- [ ] One dummy task `tasks_sync.ping()` returns "pong".
- [ ] Worker container starts and consumes from `default` queue.
- [ ] Unit test triggers task via `.delay()` and polls for result.

### TCKT-W0-004 — Next.js scaffold
Scope: frontend
Estimate: M
Depends on: W0-001
Acceptance criteria:
- [ ] Next.js 15 App Router, TypeScript strict.
- [ ] Tailwind + shadcn/ui installed.
- [ ] Base layout with dark theme default.
- [ ] `/` renders "InfluencerFlow" placeholder.
- [ ] `lib/api-client.ts` with typed fetch wrapper pointing to `/api/v1`.
- [ ] `eslint` + `prettier` configured.

### TCKT-W0-005 — Railway deployment
Scope: ops
Estimate: M
Depends on: W0-002, W0-003, W0-004
Acceptance criteria:
- [ ] Railway project created with 5 services per `ARCHITECTURE.md §14`.
- [ ] `railway.toml` committed.
- [ ] Volume `data` mounted on `api` + `worker` at `/data`.
- [ ] Staging env green: `https://<app>.railway.app/api/v1/health` returns 200.
- [ ] Next.js rewrites `/api/*` to the FastAPI service.

### TCKT-W0-006 — CI pipeline
Scope: ops
Estimate: M
Depends on: W0-002, W0-004
Acceptance criteria:
- [ ] GitHub Actions workflow: lint, typecheck, test for both `api/` and `web/`.
- [ ] PR blocked on failing checks.
- [ ] Playwright smoke test skeleton (no real tests yet, just infra).

**Week 0 exit criteria:** Railway staging boots, `/health` green, CI green on main.

---

## 4. Week 1 — Auth, Sync, Previews

> **Goal:** Juan can log in, connect Google Drive, click Resync, and see thumbnails of his photos.

### TCKT-W1-001 — User seed + bcrypt
Scope: backend
Estimate: S
Depends on: W0-002
Acceptance criteria:
- [ ] Alembic migration creates `users` table.
- [ ] CLI script `scripts/seed_user.py` inserts single user from env `SINGLE_USER_EMAIL` + `SINGLE_USER_PASSWORD`.
- [ ] Password hashed with bcrypt cost 12.
- [ ] Running script twice is idempotent (no duplicate).

### TCKT-W1-002 — NextAuth credentials login
Scope: full-stack
Estimate: M
Depends on: W1-001
Acceptance criteria:
- [ ] `/login` page with email + password form.
- [ ] NextAuth credentials provider calls `POST /api/v1/auth/login`.
- [ ] FastAPI validates bcrypt, returns JWT.
- [ ] JWT stored in HttpOnly cookie.
- [ ] Middleware guards `/dashboard`.
- [ ] `GET /api/v1/auth/me` returns user info.
- [ ] Logout clears cookie.

### TCKT-W1-003 — Rate limit login
Scope: backend
Estimate: S
Depends on: W1-002
Acceptance criteria:
- [ ] `slowapi` limits `/auth/login` to 5 attempts per 15 min per IP.
- [ ] Returns 429 with clear message.
- [ ] Unit test covers the limit.

### TCKT-W1-004 — Storage credentials schema
Scope: backend
Estimate: S
Depends on: W0-002
Acceptance criteria:
- [ ] Alembic migration creates `storage_credentials`.
- [ ] OAuth refresh tokens encrypted at rest with Fernet (key in env).
- [ ] Repository methods: `upsert`, `get_by_user_and_provider`, `delete`.

### TCKT-W1-005 — Google Drive OAuth flow
Scope: full-stack
Estimate: L
Depends on: W1-004
Acceptance criteria:
- [ ] `POST /api/v1/storage/google/oauth/start` returns consent URL.
- [ ] `GET /api/v1/storage/google/oauth/callback` exchanges code for tokens, stores in `storage_credentials`.
- [ ] Scope: `drive.readonly`.
- [ ] `DELETE /api/v1/storage/google-drive` revokes and deletes local record.
- [ ] Dashboard shows "Connect Google Drive" button → "Connected ✓" after success.
- [ ] Manual test with a real Google account passes.

### TCKT-W1-006 — Sessions table + create session
Scope: backend
Estimate: S
Depends on: W1-005
Acceptance criteria:
- [ ] Alembic migration creates `sessions`.
- [ ] `POST /api/v1/sessions` accepts `{cloud_provider, cloud_folder_id, cloud_folder_name}`, returns session.
- [ ] `GET /api/v1/sessions` lists user sessions, newest first.
- [ ] `DELETE /api/v1/sessions/{id}` cascades (sets `status=deleted` + schedules cleanup task).

### TCKT-W1-007 — Folder picker UI
Scope: frontend
Estimate: M
Depends on: W1-005, W1-006
Acceptance criteria:
- [ ] `/dashboard/new` lets Juan paste a Google Drive folder URL or ID.
- [ ] Backend endpoint `GET /api/v1/storage/google/folders/{id}` validates access and returns folder metadata.
- [ ] On confirm, creates a session and redirects to `/session/{id}`.

### TCKT-W1-008 — Assets table
Scope: backend
Estimate: S
Depends on: W1-006
Acceptance criteria:
- [ ] Alembic migration creates `assets` with all columns per `ARCHITECTURE.md §4.1`.
- [ ] Indexes on `(session_id)`, `(session_id, taken_at)`, `(session_id, phash)`.
- [ ] Repository with CRUD.

### TCKT-W1-009 — Google Drive listing & download
Scope: backend
Estimate: L
Depends on: W1-008
Acceptance criteria:
- [ ] `integrations/google_drive.py` implements `list_folder_recursive(folder_id)` with pagination.
- [ ] `download_file(file_id, dest_path)` streams with resumable support.
- [ ] Token refresh handled transparently.
- [ ] Rate limited to 8 req/s (token bucket).
- [ ] Unit tests with mocked Google API.

### TCKT-W1-010 — Filename parser library
Scope: backend
Estimate: M
Depends on: W0-002
Acceptance criteria:
- [ ] `lib/filename_parser.py` loads `config/filename_patterns.yaml` at startup.
- [ ] `parse(filename)` returns `{pattern_name, date?, sequence?}` or `None`.
- [ ] `parse_folder(name)` similarly for folders.
- [ ] Unit tests for every pattern in the YAML.
- [ ] Fallback logged when no pattern matches.

### TCKT-W1-011 — Preview generation library
Scope: backend
Estimate: L
Depends on: W0-002
Acceptance criteria:
- [ ] `lib/preview.py` has `generate(source, tier)` using configs from `preview.config` (mirror of TS).
- [ ] Handles JPEG, HEIC (pyheif), RAW (rawpy), PNG, TIFF.
- [ ] Preserves aspect ratio; longest side capped by tier.
- [ ] Corrects orientation from EXIF.
- [ ] Strips EXIF on thumbnails; keeps on preview.
- [ ] Writes to `/data/previews/{session_id}/{asset_id}_{tier}.jpg`.
- [ ] Unit tests on fixture images.

### TCKT-W1-012 — EXIF extraction
Scope: backend
Estimate: S
Depends on: W1-011
Acceptance criteria:
- [ ] `lib/exif.py` returns `{datetime_original, gps_lat, gps_lng, camera, lens, iso, aperture, shutter}`.
- [ ] Works on HEIC, JPEG, RAW formats used in fixtures.
- [ ] Unit tests.

### TCKT-W1-013 — Sync task orchestrator
Scope: backend
Estimate: L
Depends on: W1-009, W1-010, W1-011, W1-012
Acceptance criteria:
- [ ] `tasks_sync.resync_session(session_id)`:
  1. Wipes existing DB rows and files for the session.
  2. Lists cloud folder.
  3. Spawns `download_asset` group.
  4. On completion, spawns preview + EXIF group per asset.
  5. Updates `session.status` transitions: `pending → syncing → ready` (or `error`).
- [ ] Idempotent: re-running wipes cleanly.
- [ ] Integration test with a fake Google Drive adapter + 5 fixture images.

### TCKT-W1-014 — SSE progress events
Scope: full-stack
Estimate: M
Depends on: W1-013
Acceptance criteria:
- [ ] Celery tasks publish `sync.progress` events to Redis pub/sub.
- [ ] `GET /api/v1/events/session/{id}` streams SSE.
- [ ] Frontend hook `useSessionEvents(sessionId)` consumes and updates state.
- [ ] Session page shows live progress bar + current filename.

### TCKT-W1-015 — Asset thumbnail/preview endpoints
Scope: backend
Estimate: S
Depends on: W1-011
Acceptance criteria:
- [ ] `GET /api/v1/assets/{id}/thumbnail` streams the thumbnail.
- [ ] `GET /api/v1/assets/{id}/preview` streams the preview.
- [ ] Proper cache headers (`Cache-Control: private, max-age=3600`).
- [ ] 404 if missing.

### TCKT-W1-016 — Session page: basic asset grid
Scope: frontend
Estimate: M
Depends on: W1-015
Acceptance criteria:
- [ ] `/session/{id}` lists all assets as a responsive grid of thumbnails.
- [ ] Shows EXIF-date badges.
- [ ] While `status=syncing`, shows progress via SSE.
- [ ] Empty state + error state handled.

**Week 1 exit criteria:** Juan logs in → connects Drive → creates session → Resync runs → thumbnails appear.

---

## 5. Week 2 — Grouping & Review UI

> **Goal:** Juan opens a session and sees his photos grouped into potential Instagram posts.

### TCKT-W2-001 — Groups + group_assets tables
Scope: backend
Estimate: S
Depends on: W1-008
Acceptance criteria:
- [ ] Alembic migration for `groups` and `group_assets`.
- [ ] Repositories with CRUD + position management.

### TCKT-W2-002 — Deterministic grouping service
Scope: backend
Estimate: L
Depends on: W2-001, W1-010
Acceptance criteria:
- [ ] `services/grouping_service.py` implements rules from `ARCHITECTURE.md §9.5` + `filename_patterns.yaml.grouping_rules`.
- [ ] Algorithm: sort assets by `taken_at`, scan → new group when gap > 2h OR GPS distance > 500m.
- [ ] Folder-pattern-derived groups take priority when matched.
- [ ] Idempotent: wipes prior `auto_generated=true` groups before re-running.
- [ ] Unit tests with fixtures covering: same-day-single-location, multi-day, GPS-far-jumps, timestamp-only (no GPS).
- [ ] Automatically runs at end of Resync.

### TCKT-W2-003 — Group endpoints
Scope: backend
Estimate: M
Depends on: W2-002
Acceptance criteria:
- [ ] `GET /api/v1/sessions/{id}/groups` returns groups + nested assets (ordered).
- [ ] `POST /api/v1/sessions/{id}/groups/regroup-deterministic` re-runs rules.
- [ ] `PATCH /api/v1/groups/{id}` supports rename + reorder.
- [ ] `POST /api/v1/groups` creates empty group.
- [ ] `DELETE /api/v1/groups/{id}` returns assets to pool (ungrouped).
- [ ] `POST /api/v1/groups/{id}/assets` adds asset at position.
- [ ] `DELETE /api/v1/groups/{id}/assets/{asset_id}` removes.

### TCKT-W2-004 — pHash computation
Scope: backend
Estimate: S
Depends on: W1-011
Acceptance criteria:
- [ ] `lib/phash.py` computes 64-bit perceptual hash from a thumbnail.
- [ ] Stored in `assets.phash` as hex string.
- [ ] Added as a step in the sync pipeline.
- [ ] Unit test confirms identical images produce identical hashes.

### TCKT-W2-005 — Near-duplicate clustering
Scope: backend
Estimate: M
Depends on: W2-004
Acceptance criteria:
- [ ] Within a group, cluster assets by Hamming distance < threshold from config.
- [ ] Cluster representative = highest aesthetic score (fallback: first in time).
- [ ] Exposed via `GET /api/v1/groups/{id}` with `near_duplicate_cluster_id` on each asset.
- [ ] Unit test: two nearly-identical fixtures cluster together; different fixture does not.

### TCKT-W2-006 — Local face detection
Scope: backend
Estimate: M
Depends on: W1-011
Acceptance criteria:
- [ ] `lib/face_detect.py` uses `face_recognition` HOG model on thumbnails.
- [ ] Returns list of `{bbox, confidence}`.
- [ ] Populates `assets.has_face` during sync.
- [ ] Performance: under 500ms per thumbnail.
- [ ] Unit tests on fixture images with/without faces.

### TCKT-W2-007 — Review grid UI
Scope: frontend
Estimate: L
Depends on: W2-003, W2-005
Acceptance criteria:
- [ ] `/session/{id}` now shows groups as stacked carousels.
- [ ] Each group: title (editable inline), count, grid of assets.
- [ ] Near-duplicates collapsed by default; click to expand.
- [ ] Each card shows: thumbnail, face indicator icon, video indicator icon.
- [ ] Quick-reject button on each card (sets `asset.status = 'rejected'`).
- [ ] Drag-and-drop between groups (use `dnd-kit`).
- [ ] Drag to reorder groups.
- [ ] "Re-group" button (deterministic, free).

### TCKT-W2-008 — Move assets between groups UX
Scope: frontend
Estimate: M
Depends on: W2-007
Acceptance criteria:
- [ ] Drag asset between groups triggers optimistic update + API call.
- [ ] Rollback on failure with toast error.
- [ ] Position preserved (drop index translates to `group_assets.position`).

### TCKT-W2-009 — Ungrouped pool
Scope: full-stack
Estimate: S
Depends on: W2-007
Acceptance criteria:
- [ ] Assets not in any group appear in an "Ungrouped" drawer at the bottom.
- [ ] Can drag from/to any group.

**Week 2 exit criteria:** Session view shows grouped photos, near-dupes collapse, manual reorganization works, no AI used yet.

---

## 6. Week 3 — Edit View & Color Corrections

> **Goal:** Juan opens a photo, sees a before/after slider, picks a color correction from 3 local proposals, accepts it.

### TCKT-W3-001 — Edit versions table
Scope: backend
Estimate: S
Depends on: W1-008
Acceptance criteria:
- [ ] Alembic migration for `edit_versions`.
- [ ] Repository with create, get_by_asset, get_current.
- [ ] On asset creation, an initial "version 0" (original, no changes) is inserted.

### TCKT-W3-002 — Color operations library (local)
Scope: backend
Estimate: L
Depends on: W0-002
Acceptance criteria:
- [ ] `lib/color_ops.py` implements: exposure, contrast, white balance (temp/tint), HSL, highlights/shadows.
- [ ] Applies in documented order from `ARCHITECTURE.md §9.2`.
- [ ] Each operation takes a PIL Image + params dict → returns new Image.
- [ ] Idempotent: applying identity params returns unchanged image.
- [ ] Unit tests comparing pixel values against golden fixtures.

### TCKT-W3-003 — LUT application
Scope: backend
Estimate: M
Depends on: W3-002
Acceptance criteria:
- [ ] `lib/color_ops.py` has `apply_lut(image, cube_path)` using `colour-science`.
- [ ] 3 default `.cube` files ship in `api/assets/luts/`:
  - `golden_hour.cube`
  - `editorial_neutral.cube`
  - `cinematic_moody.cube`
- [ ] Unit test applies each and writes output for visual inspection.

### TCKT-W3-004 — Local color proposal service
Scope: backend
Estimate: M
Depends on: W3-003
Acceptance criteria:
- [ ] `services/editing_service.py` exposes `propose_colors_local(asset_id)`.
- [ ] Returns 3 proposals:
  - Golden Hour Warm: warm LUT + subtle exposure/sat tweaks.
  - Editorial Neutral: neutral LUT + contrast boost.
  - Cinematic Moody: moody LUT + shadow tint.
- [ ] Each proposal contains: preset name, adjustments dict, generated preview JPG (applied to the low-res preview only).
- [ ] Unit test verifies all 3 previews are generated.

### TCKT-W3-005 — Color suggestion endpoint
Scope: backend
Estimate: S
Depends on: W3-004
Acceptance criteria:
- [ ] `POST /api/v1/assets/{id}/edits/suggest` body `{corrections: ["color"], mode: "local"}`.
- [ ] Returns 3 candidate `edit_versions` (pending, not yet accepted).
- [ ] Each candidate has a preview URL for the slider UI.
- [ ] Mode `ai` returns 501 for now (wired in W4).

### TCKT-W3-006 — Accept / reject edit
Scope: backend
Estimate: M
Depends on: W3-005
Acceptance criteria:
- [ ] `POST /api/v1/edits/{id}/accept` body `{selected_corrections: ["color"]}` marks `user_decision=accepted`.
- [ ] `POST /api/v1/edits/{id}/reject` body `{regenerate: bool}`.
- [ ] Accepted version becomes the "current" chain tip for that asset.
- [ ] Rejecting with `regenerate=true` spawns a new candidate (for W3: re-runs local; for AI: costs tokens w/ confirmation).
- [ ] History preserved in `edit_versions`.

### TCKT-W3-007 — Changes log text generation
Scope: backend
Estimate: S
Depends on: W3-006
Acceptance criteria:
- [ ] When a version is accepted, `changes_log_text` is rendered from `corrections_applied_json` as human-readable bullets in Spanish.
- [ ] Example formatting matches `CLAUDE.md §6 Step 6`.
- [ ] Unit test for the renderer.

### TCKT-W3-008 — Edit view page
Scope: frontend
Estimate: L
Depends on: W3-005
Acceptance criteria:
- [ ] `/edit/{assetId}` full-screen edit experience.
- [ ] Left panel: current preview. Right panel: proposed preview.
- [ ] Before/after slider (touch + mouse), built on `react-compare-slider`.
- [ ] Right side cycles through proposals with arrows or tabs.
- [ ] Proposal name + changes log visible.
- [ ] Buttons: **Accept**, **Reject → Regenerate**, **Reject → Manual**.
- [ ] Cost badge on any mode that has a price tag (none yet in W3, placeholder UI).

### TCKT-W3-009 — Correction picker (multi-category)
Scope: frontend
Estimate: M
Depends on: W3-008
Acceptance criteria:
- [ ] Edit view shows 4 correction tabs: Color, Crop, Remove Objects, Face.
- [ ] Only Color is active in W3; others show "coming next week" placeholder.
- [ ] Each tab has a mode selector: 🧑 Manual / 🆓 Local / 🤖 AI.
- [ ] AI mode disabled until W4.

### TCKT-W3-010 — Apply to full-res on accept
Scope: backend
Estimate: M
Depends on: W3-006
Acceptance criteria:
- [ ] When accepted, `tasks_editing.apply_corrections(edit_version_id)` runs in background.
- [ ] Reads original full-res, applies same color params, writes to `/data/edits/...`.
- [ ] Updates `edit_versions.output_path`.
- [ ] Emits `edit.completed` SSE.

**Week 3 exit criteria:** Juan can open any photo, see 3 color variants, accept one, and the full-res edit is saved.

---

## 7. Week 4 — Object Removal & Face Retouch

> **Goal:** Juan can remove distracting objects via Replicate and enhance faces via the manual crop→FaceApp→re-upload flow.

### TCKT-W4-001 — Claude API wrapper
Scope: backend
Estimate: M
Depends on: W0-002
Acceptance criteria:
- [ ] `integrations/claude.py` with `call(prompt_name, prompt_version, variables, model)`.
- [ ] Wraps Anthropic SDK; supports vision content.
- [ ] Checks `ai_cache` by SHA256 key before calling.
- [ ] Writes to `cost_log` and `ai_cache` after successful calls.
- [ ] Unit tests with mocked SDK.

### TCKT-W4-002 — ai_cache table
Scope: backend
Estimate: S
Depends on: W0-002
Acceptance criteria:
- [ ] Alembic migration for `ai_cache`.
- [ ] Repository with `get`, `set`, `invalidate_by_prefix`.

### TCKT-W4-003 — Replicate wrapper
Scope: backend
Estimate: M
Depends on: W4-002
Acceptance criteria:
- [ ] `integrations/replicate.py` with `run(model, inputs)`.
- [ ] Supports polling until complete.
- [ ] Caches by SHA256 of `model_version + inputs_hash`.
- [ ] Writes to `cost_log`.
- [ ] Concurrency cap of 3 via semaphore.

### TCKT-W4-004 — Object-removal mask suggestion (Claude)
Scope: backend
Estimate: M
Depends on: W4-001
Acceptance criteria:
- [ ] `services/editing_service.py` has `suggest_removal_candidates(asset_id)`.
- [ ] Uses prompt `PROMPT_OBJECT_REMOVAL_V1` from `PROMPTS.md §4`.
- [ ] Returns list of `{label, bbox, confidence}`.
- [ ] Unit tests with fixture response.

### TCKT-W4-005 — LaMa inpainting via Replicate
Scope: backend
Estimate: L
Depends on: W4-003
Acceptance criteria:
- [ ] `tasks_editing.remove_objects(asset_id, bboxes)`:
  1. Loads preview (or full-res if `apply_to_full=true`).
  2. Builds binary mask.
  3. Calls Replicate LaMa.
  4. Saves output.
  5. Creates `edit_version`.
- [ ] Costs logged with model name + estimated dollars.
- [ ] Integration test against fixture with mocked Replicate.

### TCKT-W4-006 — Object removal UI
Scope: frontend
Estimate: L
Depends on: W4-004, W4-005
Acceptance criteria:
- [ ] In Edit view, "Remove Objects" tab shows candidate bboxes overlaid on preview.
- [ ] Each bbox has a checkbox (default: respect `recommend_remove`).
- [ ] Confirmation modal shows cost estimate before running.
- [ ] After run, preview refreshes via SSE.

### TCKT-W4-007 — Cost estimate endpoint
Scope: backend
Estimate: M
Depends on: W4-001, W4-003
Acceptance criteria:
- [ ] `POST /api/v1/cost/estimate` body `{operation, inputs}`.
- [ ] Returns `{tokens_in, tokens_out, dollars}` based on heuristics per operation.
- [ ] Covered operations: `grouping_ai`, `color_ai`, `crop_ai`, `object_removal`, `description`, `nima`.
- [ ] Unit tests with golden values.

### TCKT-W4-008 — Cost confirmation modal
Scope: frontend
Estimate: M
Depends on: W4-007
Acceptance criteria:
- [ ] Reusable `<CostConfirm>` component.
- [ ] Takes operation type + inputs, calls `/cost/estimate`, shows modal.
- [ ] Displays: operation name, estimate in USD, current session total, budget remaining.
- [ ] Buttons: "Cancel" / "Continue".
- [ ] Wired into object removal flow as first consumer.

### TCKT-W4-009 — face_crops table
Scope: backend
Estimate: S
Depends on: W1-008
Acceptance criteria:
- [ ] Alembic migration for `face_crops`.
- [ ] Repository with CRUD.

### TCKT-W4-010 — Face crop from full-res
Scope: backend
Estimate: M
Depends on: W2-006, W4-009
Acceptance criteria:
- [ ] `POST /api/v1/assets/{id}/face-crops`:
  1. Detects faces on full-res using dlib or `face_recognition`.
  2. Expands bbox by 20%.
  3. Saves crop as PNG to `/data/face_crops/...`.
  4. Stores 68-point landmarks in `landmarks_json`.
  5. Returns list of crops with download URLs.
- [ ] `GET /api/v1/face-crops/{id}/download` streams the PNG.

### TCKT-W4-011 — Face crop upload endpoint
Scope: backend
Estimate: S
Depends on: W4-010
Acceptance criteria:
- [ ] `POST /api/v1/face-crops/{id}/upload-corrected` multipart upload.
- [ ] Validates: PNG/JPG, max 20 MB, same aspect ratio as the original crop.
- [ ] Stores to `user_uploaded_path`, updates `status = 'uploaded'`.

### TCKT-W4-012 — Poisson seamless blend
Scope: backend
Estimate: L
Depends on: W4-011
Acceptance criteria:
- [ ] `lib/blend.py` with `blend_face(original_path, crop_path, user_crop_path, landmarks, output_path)`.
- [ ] Runs landmark detection on uploaded crop.
- [ ] Computes similarity transform → aligns uploaded to original landmarks.
- [ ] Builds elliptical mask; runs `cv2.seamlessClone` (NORMAL_CLONE).
- [ ] Fallback: Gaussian-blurred alpha mask copy-paste if landmark match fails.
- [ ] Unit tests with fixtures.
- [ ] `tasks_editing.blend_face(face_crop_id)` orchestrates, emits SSE.

### TCKT-W4-013 — Face retouch UI flow
Scope: frontend
Estimate: L
Depends on: W4-010, W4-011, W4-012
Acceptance criteria:
- [ ] "Face" tab in Edit view shows detected faces overlaid.
- [ ] "Download crop" button per face → triggers backend crop + downloads PNG.
- [ ] "Upload corrected" button with file input.
- [ ] After upload, "Blend" button triggers backend blend.
- [ ] Preview refreshes via SSE when blend completes.
- [ ] UI handles the 3 states: `cropped`, `uploaded`, `blended`.

**Week 4 exit criteria:** Juan can remove objects from a photo, and can complete a full face retouch round-trip through FaceApp.

---

## 8. Week 5 — Descriptions, Export, Cost Tracking

> **Goal:** Juan generates a caption via Claude, downloads a ZIP, and sees all his costs.

### TCKT-W5-001 — descriptions table
Scope: backend
Estimate: S
Depends on: W2-001
Acceptance criteria:
- [ ] Alembic migration for `descriptions`.
- [ ] Repository with CRUD + `set_current`.

### TCKT-W5-002 — Past-captions seed mechanism
Scope: backend
Estimate: S
Depends on: W5-001
Acceptance criteria:
- [ ] Config file `api/assets/style_seed.txt` where Juan can paste past IG captions (one per line or blank-line-separated).
- [ ] Loaded on demand by the description service as style reference.
- [ ] Optional: if file missing, service proceeds without style reference.

### TCKT-W5-003 — Tile-packing library
Scope: backend
Estimate: M
Depends on: W1-011
Acceptance criteria:
- [ ] `lib/tile_pack.py` with `pack_thumbnails(thumbnail_paths, cols, padding) -> bytes`.
- [ ] Deterministic output for same inputs.
- [ ] Adds numbered labels to each tile (top-left corner).
- [ ] Max 9 per tile per config.
- [ ] Unit tests.

### TCKT-W5-004 — Description generation service
Scope: backend
Estimate: L
Depends on: W4-001, W5-002, W5-003
Acceptance criteria:
- [ ] `services/description_service.py` has `generate(group_id, custom_prompt)`.
- [ ] Builds Claude call: tile-packed previews + EXIF-derived location + date + style seed + custom prompt.
- [ ] Uses `PROMPT_DESCRIPTION_V1` from `PROMPTS.md §5`.
- [ ] Saves result to `descriptions` with `is_current=true`, unsets previous current for the group.
- [ ] Logs cost.

### TCKT-W5-005 — Description endpoints
Scope: backend
Estimate: S
Depends on: W5-004
Acceptance criteria:
- [ ] `POST /api/v1/groups/{id}/descriptions/generate` body `{custom_prompt?}`.
- [ ] `GET /api/v1/groups/{id}/descriptions` returns history newest-first.
- [ ] `POST /api/v1/descriptions/{id}/set-current`.

### TCKT-W5-006 — Description UI
Scope: frontend
Estimate: M
Depends on: W5-005
Acceptance criteria:
- [ ] Group detail view has a "Caption" section.
- [ ] "Generate" button (with cost confirmation).
- [ ] Free-text input next to Generate for custom guidance.
- [ ] Shows current caption in a scrollable text area.
- [ ] History dropdown to switch versions.
- [ ] "Copy to clipboard" button.

### TCKT-W5-007 — ZIP export builder
Scope: backend
Estimate: L
Depends on: W3-010
Acceptance criteria:
- [ ] `tasks_export.build_zip(group_id)`:
  1. For each asset in group (in position order), resolve the current `edit_versions.output_path` (or original if no edits).
  2. Rename to `{NN}_{place_or_date}.{ext}` where NN is 2-digit position.
  3. ZIP into `/data/exports/{session_id}/{group_id}.zip`.
- [ ] Writes row to a new `exports` table (small schema) or reuses job id + path.
- [ ] Emits `export.ready` SSE.

### TCKT-W5-008 — Export endpoints
Scope: backend
Estimate: M
Depends on: W5-007
Acceptance criteria:
- [ ] `POST /api/v1/groups/{id}/export` returns `{job_id}`.
- [ ] `GET /api/v1/exports/{job_id}` returns `{status, download_url?}`.
- [ ] `GET /api/v1/exports/{job_id}/download` streams the ZIP (HMAC-signed URL, 15-min TTL).

### TCKT-W5-009 — Export UI
Scope: frontend
Estimate: S
Depends on: W5-008
Acceptance criteria:
- [ ] "Download ZIP" button on group detail view.
- [ ] Spinner while building; download starts automatically when ready.
- [ ] Toast "Export listo" with filename.

### TCKT-W5-010 — cost_log table + endpoint
Scope: full-stack
Estimate: M
Depends on: W4-001, W4-003
Acceptance criteria:
- [ ] Alembic migration for `cost_log` (if not already created earlier).
- [ ] `GET /api/v1/sessions/{id}/cost` returns `{total_dollars, by_operation: [{operation, count, dollars}]}`.
- [ ] Session header in UI shows running total.
- [ ] Settings → Cost page shows detailed breakdown.

### TCKT-W5-011 — Budget guard
Scope: full-stack
Estimate: M
Depends on: W5-010
Acceptance criteria:
- [ ] Env `SESSION_BUDGET_USD` (default 10) controls soft cap.
- [ ] If a new paid op would exceed the cap, the confirmation modal shows an orange "Budget exceeded" banner.
- [ ] User can still proceed (soft cap only).
- [ ] Hard cap env `SESSION_HARD_CAP_USD` (default 50) → blocks further paid ops until cleared.

**Week 5 exit criteria:** Juan can generate a caption, download a ZIP with correctly-named final images, and see every dollar spent.

---

## 9. Week 6 — Polish & Dogfood

> **Goal:** Use InfluencerFlow on a real trip. Fix what annoys.

### TCKT-W6-001 — Loading & error states audit
Scope: frontend
Estimate: M
Depends on: everything
Acceptance criteria:
- [ ] Every async UI interaction has a loading state.
- [ ] Every failure shows a toast with a retry action when applicable.
- [ ] No uncaught promise warnings in console.

### TCKT-W6-002 — Keyboard shortcuts
Scope: frontend
Estimate: S
Depends on: W3-008
Acceptance criteria:
- [ ] Edit view: `←/→` cycle proposals, `Enter` accept, `Esc` back, `1/2/3/4` switch correction tabs.
- [ ] Review grid: `X` quick-reject focused asset.

### TCKT-W6-003 — Spanish/English toggle
Scope: frontend
Estimate: M
Depends on: —
Acceptance criteria:
- [ ] i18n scaffold with `next-intl`.
- [ ] Settings page has language toggle; persists in localStorage.
- [ ] All visible copy externalized to `messages/{es,en}.json`.
- [ ] Default: Spanish.

### TCKT-W6-004 — Playwright end-to-end smoke
Scope: ops
Estimate: L
Depends on: W5-009
Acceptance criteria:
- [ ] Playwright test per the flow in `ARCHITECTURE.md §16.3`.
- [ ] Runs on every PR in CI (against docker-compose).
- [ ] Uses mocked Google Drive adapter + fixture images + mocked Replicate.

### TCKT-W6-005 — Performance pass
Scope: full-stack
Estimate: M
Depends on: everything
Acceptance criteria:
- [ ] Thumbnails lazy-loaded with IntersectionObserver.
- [ ] Preview fetch prefetched on hover.
- [ ] Server-side pagination for sessions with >500 assets.
- [ ] Vitals: LCP < 2.5s on review grid with 200 assets (local network).

### TCKT-W6-006 — Secrets rotation drill
Scope: ops
Estimate: S
Depends on: W0-005
Acceptance criteria:
- [ ] Document `docs/OPERATIONS.md` with: how to rotate `NEXTAUTH_SECRET`, `JWT_SECRET`, Google OAuth client, Claude key, Replicate token.
- [ ] Practice rotating Claude key on staging.

### TCKT-W6-007 — Real-trip dogfood
Scope: end-user
Estimate: L
Depends on: everything
Acceptance criteria:
- [ ] Juan uploads a real trip folder (~100 files).
- [ ] Goes through the entire flow.
- [ ] Exports ZIP + captions for at least 3 posts.
- [ ] Posts at least one to Instagram.
- [ ] Fills `docs/DOGFOOD_NOTES.md` with friction points, bugs, and feature gaps.

### TCKT-W6-008 — Fix top 5 dogfood issues
Scope: full-stack
Estimate: L
Depends on: W6-007
Acceptance criteria:
- [ ] Triage `DOGFOOD_NOTES.md`.
- [ ] Fix the 5 highest-impact issues.
- [ ] Log the rest in a V1 backlog.

**Week 6 exit criteria:** Juan has posted to Instagram with InfluencerFlow. MVP declared done.

---

## 10. Out of Scope for MVP

Explicitly not built in these 6 weeks. Tracked for V1 or Phase 2:

- Mega integration (deferred to V1).
- AI grouping refinement (deferred to V1).
- Replicate NIMA aesthetic scoring (deferred to V1).
- GFPGAN-based AI face enhancement (evaluated; excluded; manual FaceApp is better).
- Automated video editing (pure manual round-trip for MVP).
- Instagram Graph API direct posting.
- Multi-user support and anything related to auth scaling.
- Billing / subscription system.
- Privacy & data retention policy documentation.
- Marketing / landing page.
- Learning from Juan's accepted edits to personalize future suggestions.
- Edit history navigation UI (data is stored, no UI yet).
- GPU workers for on-prem inpainting.

---

## 11. Risk Register

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| 1 | HEIC/RAW handling bugs on Railway containers | Med | High | Pin `pyheif` + `rawpy` versions; fixtures cover both formats; test on Railway early in W1 |
| 2 | Google Drive API rate limits hit during sync of large folders | Med | Med | Token bucket 8 req/s; resumable downloads; start with 100-file sessions |
| 3 | Replicate cold starts cause long waits | High | Low | UI shows progress; user confirms cost ahead; caching reduces repeat calls |
| 4 | Poisson blending artifacts on non-matching face uploads | High | Med | Fallback mask copy-paste; document that aggressive FaceApp edits may show seams |
| 5 | Railway volume size exceeded by a large trip | Med | High | Enforce per-session cleanup on Resync; monitor disk in ops doc; evict oldest sessions on demand |
| 6 | Claude cost runs away from a bug in caching | Low | High | Cost cap env `SESSION_HARD_CAP_USD` blocks at $50; daily cost digest emailed (V1) |
| 7 | pHash false positives collapse distinct photos | Med | Low | Threshold configurable; clusters always expandable in UI |
| 8 | OAuth token revoked mid-sync | Low | Med | Refresh on 401; clear session and show reconnect banner |
| 9 | Railway pricing changes for Postgres/Redis | Low | Med | Can swap Postgres to Supabase free tier with 1-line DSN change |
| 10 | Scope creep from dogfood feedback in W6 | High | Med | Fix only top 5; everything else goes to V1 backlog |

---

## 12. Dogfood Checklist

Pre-flight before the real-trip run in W6:

- [ ] Backup of the test Drive folder taken (read-only scope is already protective, but still).
- [ ] Railway disk has at least 10 GB free.
- [ ] `SESSION_BUDGET_USD=10` set.
- [ ] Claude + Replicate API keys valid and within quota.
- [ ] Fresh Resync dry-run on a 10-file test folder passes.
- [ ] `DOGFOOD_NOTES.md` template ready in repo.

Post-run:

- [ ] Note the total dollar cost.
- [ ] Note the total wall-clock time.
- [ ] Note the active (hands-on) time.
- [ ] List the top 10 friction points.
- [ ] Decide: V1 go/no-go based on experience.
