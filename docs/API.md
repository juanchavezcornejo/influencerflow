# REST API Reference

Base URL: `/api/v1`
Auth: `Authorization: Bearer <jwt>` header required on all endpoints except `POST /auth/login`, `GET /health`, and `GET /health/ready`.
Rate limit: 200 requests/minute per IP (global default). `POST /auth/login` is stricter: 5 requests per 15 minutes per IP.

## Standard Shapes

**Error response:**
```json
{ "detail": "human-readable message" }
```

**Cost estimate shape:**
```json
{ "dollars": 0.05, "tokensIn": 2000, "tokensOut": 500, "model": "claude-sonnet-4-6" }
```

---

## /auth

### POST /auth/login
Auth required: No
Rate limit: 5/15 minutes

**Body:**
```json
{ "email": "user@example.com", "password": "secret" }
```

**Response 200:**
```json
{ "accessToken": "<jwt>" }
```

**Response 401:**
```json
{ "detail": "Invalid email or password" }
```

---

### GET /auth/me
Auth required: Yes (Bearer token)

**Response 200:**
```json
{ "id": "uuid", "email": "user@example.com" }
```

**Response 401:** Missing or invalid token.
**Response 404:** User not found.

---

### POST /auth/logout
Auth required: No (but harmless if sent)

Clears the `Authorization` cookie on the client.

**Response 200:**
```json
{ "message": "logged out" }
```

---

## /sessions

### POST /sessions
Auth required: Yes

**Body:**
```json
{
  "cloud_provider": "google_drive",
  "cloud_folder_id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs",
  "cloud_folder_name": "Bali Trip 2026"
}
```

**Response 200:**
```json
{
  "id": "uuid",
  "cloud_provider": "google_drive",
  "cloud_folder_id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs",
  "cloud_folder_name": "Bali Trip 2026",
  "status": "pending",
  "created_at": "2026-04-17T10:00:00"
}
```

Side effects: Creates a session row in the database. Temp files and preview generation are triggered separately.

---

### GET /sessions
Auth required: Yes

Lists all sessions belonging to the current user.

**Response 200:** Array of session objects (same shape as POST /sessions response).

---

### GET /sessions/{session_id}
Auth required: Yes

**Response 200:** Session object.
**Response 404:** Session not found or not owned by caller.

---

### DELETE /sessions/{session_id}
Auth required: Yes

Soft-deletes the session.

**Response 200:**
```json
{ "message": "Session deleted" }
```

**Response 404:** Session not found or not owned by caller.

Side effects: Marks session deleted. Temp file cleanup is queued (TODO, not yet implemented).

---

### GET /sessions/{session_id}/cost
Auth required: Yes

Returns cost breakdown grouped by operation type.

**Response 200:**
```json
{
  "total_dollars": 1.23,
  "by_operation": [
    { "operation": "description", "count": 3, "dollars": 0.06 },
    { "operation": "object_removal", "count": 5, "dollars": 1.17 }
  ]
}
```

**Response 404:** Session not found or not owned by caller.

---

## /assets

### GET /assets/{asset_id}/thumbnail
Auth required: Yes

Streams the 384px thumbnail JPEG for the asset.

**Response 200:** `image/jpeg` binary. Header: `Cache-Control: private, max-age=3600`.
**Response 404:** Asset or thumbnail file not found.

---

### GET /assets/{asset_id}/preview
Auth required: Yes

Streams the 1024px preview JPEG for the asset.

**Response 200:** `image/jpeg` binary. Header: `Cache-Control: private, max-age=3600`.
**Response 404:** Asset or preview file not found.

---

### PATCH /assets/{asset_id}
Auth required: Yes

Update asset fields. Currently supports updating `status`.

**Body:**
```json
{ "status": "rejected" }
```

**Response 200:**
```json
{ "message": "Updated" }
```

**Response 404:** Asset not found.

---

### GET /assets/session/{session_id}/ungrouped
Auth required: Yes

Returns all assets in the session that have not been placed in any group.

**Response 200:** Array of asset objects:
```json
[
  {
    "id": "uuid",
    "original_filename": "IMG_0042.jpg",
    "phash": "a1b2c3d4e5f6...",
    "has_face": true,
    "is_video": false,
    "status": "pending",
    "near_duplicate_cluster_id": null
  }
]
```

**Response 401:** Session not found or not owned by caller.

---

## /groups

### GET /groups/session/{session_id}/groups
Auth required: Yes

Returns all groups for a session, each with its nested assets.

**Response 200:** Array of group-detail objects:
```json
[
  {
    "id": "uuid",
    "session_id": "uuid",
    "name": "Day 1 — Beach",
    "auto_generated": true,
    "asset_count": 4,
    "order_index": 0,
    "assets": [
      {
        "id": "uuid",
        "original_filename": "IMG_0001.jpg",
        "phash": "a1b2c3d4...",
        "has_face": false,
        "is_video": false,
        "status": "pending",
        "near_duplicate_cluster_id": null
      }
    ]
  }
]
```

**Response 401:** Session not found or not owned by caller.

---

### POST /groups/session/{session_id}/groups/regroup-deterministic
Auth required: Yes

Re-runs deterministic grouping (free — no AI). Clears existing groups and rebuilds based on EXIF dates, time gaps, and GPS distance.

**Body:** None

**Response 200:**
```json
{ "message": "Regrouped" }
```

**Response 401:** Session not found or not owned by caller.
Cost badge: Free (local).

---

### POST /groups
Auth required: Yes

Creates an empty manual group.

**Body:**
```json
{ "session_id": "uuid", "name": "My Custom Group" }
```

**Response 200:**
```json
{
  "id": "uuid",
  "session_id": "uuid",
  "name": "My Custom Group",
  "auto_generated": false,
  "asset_count": 0,
  "order_index": 0
}
```

**Response 401:** Session not found or not owned by caller.

---

### PATCH /groups/{group_id}
Auth required: Yes

Update a group's name or order_index. Parameters are passed as **query strings**, not a request body.

**Query params:** `name` (string, optional), `order_index` (int, optional)

Example: `PATCH /api/v1/groups/uuid?name=Sunset+Beach&order_index=2`

**Response 200:** Updated group object (without nested assets).

**Response 404:** Group not found.

---

### DELETE /groups/{group_id}
Auth required: Yes

Deletes the group. All assets in the group return to the ungrouped pool.

**Response 200:**
```json
{ "message": "Group deleted" }
```

**Response 404:** Group not found.

---

### POST /groups/{group_id}/assets/{asset_id}
Auth required: Yes

Adds an asset to a group at a given position.

**Query params:** `position` (int, default 0)

Example: `POST /api/v1/groups/uuid/assets/uuid?position=2`

**Response 200:**
```json
{ "message": "Asset added" }
```

**Response 404:** Group not found.

---

### DELETE /groups/{group_id}/assets/{asset_id}
Auth required: Yes

Removes an asset from a group (asset returns to ungrouped pool).

**Response 200:**
```json
{ "message": "Asset removed" }
```

---

### PATCH /groups/{group_id}/assets/reorder
Auth required: Yes

Reorders assets within a group. Pass the full ordered list of asset IDs as a **query string array**.

**Query params:** `asset_ids` (list of strings)

Example: `PATCH /api/v1/groups/uuid/assets/reorder?asset_ids=id1&asset_ids=id2&asset_ids=id3`

**Response 200:**
```json
{ "message": "Reordered" }
```

---

### POST /groups/{group_id}/assets/{asset_id}/move
Auth required: Yes

Moves an asset from one group to another.

**Body:**
```json
{ "from_group_id": "uuid-or-null", "position": 0 }
```

`from_group_id` is optional. If omitted, the asset is assumed to come from the ungrouped pool.

**Response 200:**
```json
{ "message": "Asset moved" }
```

---

### PATCH /groups
Auth required: Yes

Reorders groups within a session. Pass the full ordered list of group IDs as a **query string array**.

**Query params:** `group_ids` (list of strings)

Example: `PATCH /api/v1/groups?group_ids=id1&group_ids=id2`

**Response 200:**
```json
{ "message": "Groups reordered" }
```

---

## /edits

### POST /edits/assets/{asset_id}/suggest
Auth required: Yes

Generates edit proposals for an asset. Currently only `color` + `local` mode is implemented; `ai` mode returns 501.

**Body:**
```json
{
  "corrections": ["color"],
  "mode": "local"
}
```

`corrections` options: `"color"`, `"crop"`, `"remove_objects"`, `"face"`.
`mode` options: `"local"` (free), `"ai"` (token-consuming, not yet implemented in W3).

**Response 200:**
```json
{
  "proposals": [
    {
      "id": "uuid",
      "preset_name": "Golden Hour v2",
      "preview_url": "/api/v1/edits/uuid/preview",
      "changes_log_text": "- Color: LUT \"Golden Hour v2\" (temp +400K, saturation -8)"
    }
  ]
}
```

Side effects: Creates `edit_versions` rows for each proposal.
Cost badge: Free (local mode). AI mode will show cost badge when implemented.

---

### GET /edits/{edit_id}/preview
Auth required: Yes

Retrieves metadata for an edit version's preview.

**Response 200:**
```json
{
  "preview_url": "/api/v1/placeholder",
  "changes_log": "- Color: LUT \"Golden Hour v2\"..."
}
```

**Response 404:** Edit version not found.

---

### POST /edits/{edit_id}/accept
Auth required: Yes

Accepts an edit proposal and triggers full-resolution rendering in background.

**Body:**
```json
{ "selected_corrections": ["color"] }
```

**Response 200:**
```json
{
  "message": "Edit accepted",
  "version_id": "uuid",
  "changes_log": "- Color: LUT \"Golden Hour v2\"..."
}
```

Side effects: Sets `user_decision = "accepted"` on the edit version. Queues a Celery task (`apply_corrections_full_res`) to render the full-res output.

**Response 404:** Edit version not found.

---

### POST /edits/{edit_id}/reject
Auth required: Yes

Rejects an edit proposal.

**Body:**
```json
{ "regenerate": false }
```

`regenerate: true` will eventually trigger a new proposal (not yet implemented in W3 — returns informational message).

**Response 200:**
```json
{ "message": "Edit rejected" }
```

**Response 404:** Edit version not found.

---

## /face-crops

### POST /face-crops/assets/{asset_id}
Auth required: Yes

Detects faces in the asset's full-resolution image and creates crop records with 20% padding.

**Body:** None

**Response 200:** Array of face crop objects:
```json
[
  {
    "id": "uuid",
    "bbox": { "x": 100, "y": 200, "width": 150, "height": 180 },
    "status": "cropped"
  }
]
```

Returns an empty array if no faces are detected.

**Response 404:** Asset not found or has no full-res local path.
**Response 500:** Detection failed.

Side effects: Writes crop PNG files to `/data/face_crops/{asset_id}/face_{n}.png`. Creates `face_crops` rows in the database.

---

### GET /face-crops/{crop_id}/download
Auth required: Yes

Downloads the face crop PNG.

**Response 200:** `image/png` binary, filename `face_crop_{crop_id}.png`.
**Response 404:** Crop record or file not found.

---

### POST /face-crops/{crop_id}/upload-corrected
Auth required: Yes
Content-Type: `multipart/form-data`

Uploads a corrected face image (e.g., from FaceApp or external editor). Accepted types: `image/png`, `image/jpeg`.

**Form field:** `file` (binary)

**Response 200:**
```json
{ "message": "Upload successful", "status": "uploaded" }
```

**Response 400:** Unsupported file type.
**Response 404:** Crop record not found.
**Response 500:** Write failed.

Side effects: Saves file to `/data/face_crops/{asset_id}/uploads/corrected_{crop_id}.png`. Sets `status = "uploaded"` and `user_uploaded_path` on the crop record. Seamless blending into the full-res output is triggered separately (not yet automated).

---

## /descriptions

Note: This router registers at `/api/v1` directly (no additional `/descriptions` prefix).

### POST /groups/{group_id}/descriptions/generate
Auth required: Yes
Cost badge: Yes — Claude API tokens consumed.

Generates an engagement-focused Instagram caption for the group using Claude Vision + EXIF + custom prompt.

**Body:**
```json
{ "custom_prompt": "Make it casual and mention the sunset" }
```

`custom_prompt` is optional. Omit or pass `null` for default style.

**Response 200:**
```json
{
  "id": "uuid",
  "group_id": "uuid",
  "text": "Golden hour hit different here 🌅...",
  "is_current": true,
  "tokens_in": 2100,
  "tokens_out": 320,
  "created_at": "2026-04-17T10:05:00"
}
```

**Response 400:** Validation error (e.g., group has no assets).
**Response 500:** Service error.

Side effects: Creates a `descriptions` row and sets it as `is_current`. Logs cost to `cost_log`.

---

### GET /groups/{group_id}/descriptions
Auth required: Yes

Lists all description versions for a group, newest first.

**Response 200:**
```json
{
  "descriptions": [
    {
      "id": "uuid",
      "group_id": "uuid",
      "text": "Golden hour hit different...",
      "is_current": true,
      "tokens_in": 2100,
      "tokens_out": 320,
      "created_at": "2026-04-17T10:05:00"
    }
  ]
}
```

**Response 500:** Service error.

---

### POST /descriptions/{description_id}/set-current
Auth required: Yes

Promotes a previously generated description to be the current one for its group. Demotes all other descriptions in the group.

**Body:** None

**Response 200:** Updated description object (same shape as generate response).

**Response 404:** Description not found.
**Response 500:** Service error.

---

## /exports

Note: This router registers at `/api/v1` directly (no additional `/exports` prefix).

### POST /groups/{group_id}/export
Auth required: Yes

Starts a ZIP export job for a group. Returns immediately with `status: "pending"`.

**Body:** None

**Response 200:**
```json
{
  "id": "uuid",
  "session_id": "uuid",
  "group_id": "uuid",
  "status": "pending",
  "zip_path": null,
  "created_at": "2026-04-17T10:10:00",
  "completed_at": null
}
```

**Response 500:** Service error.

Side effects: Creates an `exports` row. Queues a Celery task (`build_zip`) to assemble full-res images named `01_place.jpg`, etc.

---

### GET /exports/{export_id}
Auth required: Yes

Polls export job status.

**Response 200:**
```json
{
  "id": "uuid",
  "session_id": "uuid",
  "group_id": "uuid",
  "status": "ready",
  "zip_path": "/data/exports/uuid.zip",
  "created_at": "2026-04-17T10:10:00",
  "completed_at": "2026-04-17T10:11:32"
}
```

`status` values: `pending`, `building`, `ready`, `error`.

**Response 404:** Export not found.

---

### GET /exports/{export_id}/download
Auth required: Yes

Downloads the completed ZIP file.

**Query params:** `token` (string, optional) — HMAC-signed URL token with 15-minute TTL. For MVP, token validation is a no-op; included for forward compatibility.

**Response 200:** `application/zip` binary, filename `{group_id}.zip`.
**Response 400:** Export not yet ready.
**Response 404:** Export not found or ZIP file missing.

---

## /cost

### POST /cost/estimate
Auth required: Yes

Returns a cost estimate for a planned operation before the user confirms execution.

**Body:**
```json
{
  "operation": "description",
  "inputs": { "asset_count": 6 }
}
```

`operation` values: `"object_removal"`, `"color_ai"`, `"description"`, `"ai_grouping"`, `"aesthetic_score"`.
`inputs` is optional — used by the estimator to size the estimate.

**Response 200:**
```json
{
  "tokens_in": 2000,
  "tokens_out": 500,
  "dollars": 0.05,
  "model": "claude-sonnet-4-6"
}
```

This endpoint does not consume any tokens or credits; it is a pure estimate.

---

## /settings

| Method | Path | Auth? | Body | Response |
|---|---|---|---|---|
| GET | /settings | Yes | — | Settings object |
| PATCH | /settings | Yes | SettingsPatch | Settings object |

Settings shape:
```json
{
  "claudeApiKey": "****a1b2",
  "replicateApiKey": "****c3d4",
  "googleClientId": "123456.apps.googleusercontent.com",
  "googleClientSecret": "****e5f6",
  "sessionBudgetUsd": 10.0,
  "sessionHardCapUsd": 50.0,
  "styleSeed": "Casual, sun-drenched..."
}
```

Sensitive keys masked in GET (last 4 chars visible). Send full value in PATCH to update; omit field to leave unchanged.

---

## /events (SSE)

### GET /events/session/{session_id}
Auth required: Yes
Content-Type: `text/event-stream`

Streams real-time progress events for a session. Polls session status internally every second. Closes automatically when status reaches `ready` or `error`, or after 5 minutes.

Headers sent: `Cache-Control: no-cache`, `Connection: keep-alive`.

**Event shape:**
```
data: {"type": "sync.status_changed", "status": "syncing"}
```

**Event types:**

| Type | When emitted | Extra fields |
|---|---|---|
| `sync.status_changed` | Session status transitions | `status` |
| `error` | Session not found | `message` |

> Note: Additional event types (`asset_ready`, `grouping_done`, `export_progress`, `export_ready`) are planned but not yet emitted. Subscribe early and handle unknown types gracefully.

**Response 403:** Session not found or not owned by caller.

---

## /storage

### GET /storage/google/oauth/start
Auth required: No

Returns the Google OAuth consent URL to begin the Drive connection flow.

**Response 200:**
```json
{ "auth_url": "https://accounts.google.com/o/oauth2/v2/auth?..." }
```

**Response 500:** OAuth configuration error.

---

### GET /storage/google/oauth/callback
Auth required: Yes

Handles the redirect from Google. Exchange the authorization code for access + refresh tokens, then stores credentials.

**Query params:** `code` (string, required) — provided by Google redirect.

**Response 200:**
```json
{ "provider": "google_drive", "email": "" }
```

> Note: `email` field is currently empty (TODO in source).

**Response 500:** Token exchange or storage failure.

Side effects: Upserts a `storage_credentials` row with the user's Google refresh token and access token.

---

### GET /storage/google/folders/{folder_id}
Auth required: Yes

Returns metadata for a Google Drive folder (name, file count preview).

**Response 200:**
```json
{
  "id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs",
  "name": "Bali Trip 2026",
  "file_count": 147
}
```

**Response 401:** User has not connected Google Drive.
**Response 400:** Cannot access folder (wrong ID, permission denied, etc).

---

### DELETE /storage/google-drive
Auth required: Yes

Disconnects Google Drive by deleting stored OAuth credentials.

**Response 200:**
```json
{ "message": "Disconnected from Google Drive" }
```

---

## /health

### GET /health
Auth required: No

Liveness check — confirms the process is running.

**Response 200:**
```json
{ "status": "ok" }
```

---

### GET /health/ready
Auth required: No

Readiness check — confirms the database is reachable.

**Response 200:**
```json
{ "status": "ready", "db": "ok" }
```

**Response 503:**
```json
{ "status": "not_ready", "db": "error" }
```
