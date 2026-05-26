# Data Model

> Single source of truth for all DB queries. Read before touching models, migrations, or repositories.

---

## Table Reference

### users

| Column | Type | Nullable | Notes |
|---|---|---|---|
| id | String(36) | NO | UUID hex, PK |
| email | String(255) | NO | Unique, indexed |
| password_hash | String(255) | NO | bcrypt hash |
| created_at | DateTime(tz) | NO | Indexed |
| updated_at | DateTime(tz) | NO | Auto-updated on write |

---

### storage_credentials

| Column | Type | Nullable | Notes |
|---|---|---|---|
| id | String(36) | NO | UUID hex, PK |
| user_id | String(36) | NO | FK → users.id, indexed |
| provider | String(50) | NO | e.g. `"google_drive"`, indexed |
| refresh_token | Text | NO | Fernet-encrypted |
| access_token | Text | YES | Fernet-encrypted |
| created_at | DateTime(tz) | NO | Indexed |
| updated_at | DateTime(tz) | NO | Auto-updated on write |

Unique constraint: `(user_id, provider)`.

---

### sessions

| Column | Type | Nullable | Notes |
|---|---|---|---|
| id | String(36) | NO | UUID hex, PK |
| user_id | String(36) | NO | FK → users.id, indexed |
| cloud_provider | String(50) | NO | e.g. `"google_drive"` |
| cloud_folder_id | String(255) | NO | Provider's folder identifier |
| cloud_folder_name | String(255) | NO | Human-readable folder name |
| status | String(50) | NO | `pending` \| `syncing` \| `ready` \| `error` \| `deleted`; indexed |
| created_at | DateTime(tz) | NO | Indexed |
| updated_at | DateTime(tz) | NO | Auto-updated on write |

---

### assets

| Column | Type | Nullable | Notes |
|---|---|---|---|
| id | String(36) | NO | UUID hex, PK |
| session_id | String(36) | NO | FK → sessions.id, indexed |
| original_cloud_path | String(1024) | NO | Path/ID in cloud provider |
| original_filename | String(255) | NO | File name from cloud |
| preview_path | String(1024) | YES | Local path to 1024px preview |
| thumbnail_path | String(1024) | YES | Local path to 384px thumbnail |
| full_res_local_path | String(1024) | YES | Local path to downloaded original |
| exif_json | Text | YES | JSON-serialized EXIF (see JSON Field Structures) |
| gps_lat | Float | YES | Decimal degrees, indexed |
| gps_lng | Float | YES | Decimal degrees, indexed |
| taken_at | DateTime(tz) | YES | From EXIF DateTimeOriginal, indexed |
| is_video | Boolean | NO | Default `false` |
| has_face | Boolean | NO | Default `false`; set by local face_recognition |
| aesthetic_score | Float | YES | NIMA score 0–10; populated on opt-in |
| phash | String(16) | YES | Perceptual hash (hex string), indexed |
| status | String(50) | NO | `active` \| `rejected`; default `active` |
| near_duplicate_cluster_id | String(36) | YES | Groups near-duplicate assets |
| created_at | DateTime(tz) | NO | Indexed |
| updated_at | DateTime(tz) | NO | Auto-updated on write |

Composite indexes: `(session_id, taken_at)`, `(session_id, phash)`.

---

### groups

| Column | Type | Nullable | Notes |
|---|---|---|---|
| id | String(36) | NO | UUID hex, PK |
| session_id | String(36) | NO | FK → sessions.id, indexed |
| name | String(255) | NO | Display name for the group |
| auto_generated | Boolean | NO | `true` = created by deterministic/AI grouping |
| order_index | Integer | NO | Presentation order, default `0`, indexed |
| created_at | DateTime(tz) | NO | Indexed |
| updated_at | DateTime(tz) | NO | Auto-updated on write |

---

### group_assets

| Column | Type | Nullable | Notes |
|---|---|---|---|
| id | String(36) | NO | UUID hex, PK |
| group_id | String(36) | NO | FK → groups.id, indexed |
| asset_id | String(36) | NO | FK → assets.id, indexed |
| position | Integer | NO | Order within the group, indexed |
| created_at | DateTime(tz) | NO | |

Unique constraint: `(group_id, asset_id)`.

---

### edit_versions

| Column | Type | Nullable | Notes |
|---|---|---|---|
| id | String(36) | NO | UUID hex, PK |
| asset_id | String(36) | NO | FK → assets.id, indexed |
| parent_version_id | String(36) | YES | FK → edit_versions.id (self-referential) |
| created_at | DateTime(tz) | NO | Indexed |
| changes_log_text | Text | YES | Human-readable bullet list of changes |
| corrections_applied_json | Text | YES | JSON dict of corrections (see JSON Field Structures) |
| output_path | String(1024) | YES | Path to full-res output file |
| user_decision | String(50) | YES | `accepted` \| `rejected`; indexed |

---

### face_crops

| Column | Type | Nullable | Notes |
|---|---|---|---|
| id | String(36) | NO | UUID hex, PK |
| asset_id | String(36) | NO | FK → assets.id, indexed |
| bbox_json | Text | NO | Bounding box JSON (see JSON Field Structures) |
| landmarks_json | Text | YES | 68 facial landmark coordinates |
| crop_path | String(1024) | NO | Path to extracted crop PNG |
| user_uploaded_path | String(1024) | YES | Path to user-edited crop (re-upload) |
| blended_output_path | String(1024) | YES | Path to Poisson-blended final result |
| status | String(50) | NO | `cropped` \| `uploaded` \| `blended`; indexed |
| created_at | DateTime(tz) | NO | |

---

### descriptions

| Column | Type | Nullable | Notes |
|---|---|---|---|
| id | String(36) | NO | UUID hex, PK |
| group_id | String(36) | NO | FK → groups.id, indexed |
| text | Text | NO | Generated caption text |
| custom_prompt | Text | YES | User-supplied prompt override |
| model_used | String(100) | YES | e.g. `"claude-sonnet-4-6"` |
| tokens_in | Integer | YES | Input tokens consumed |
| tokens_out | Integer | YES | Output tokens produced |
| is_current | Boolean | NO | `true` for the active caption shown in UI; indexed |
| created_at | DateTime(tz) | NO | Indexed |

---

### cost_log

| Column | Type | Nullable | Notes |
|---|---|---|---|
| id | String(36) | NO | UUID hex, PK |
| session_id | String(36) | NO | FK → sessions.id, indexed |
| operation | String(100) | NO | Operation type (see Cost Log Operation Enum Values), indexed |
| model | String(100) | YES | Model identifier (Claude model slug or Replicate model) |
| tokens_in | Integer | YES | Input tokens (null for Replicate ops) |
| tokens_out | Integer | YES | Output tokens (null for Replicate ops) |
| dollars_estimate | Float | YES | Dollar cost at time of operation |
| created_at | DateTime(tz) | NO | Indexed |

---

### ai_cache

| Column | Type | Nullable | Notes |
|---|---|---|---|
| cache_key | String(64) | NO | SHA-256 of (model + prompt hash), PK |
| response_json | Text | NO | Full API response serialized to JSON |
| model_used | String(100) | YES | Model that produced the response |
| tokens_in | Integer | YES | Input tokens of the cached call |
| tokens_out | Integer | YES | Output tokens of the cached call |
| created_at | DateTime(tz) | NO | Indexed |

---

### exports

| Column | Type | Nullable | Notes |
|---|---|---|---|
| id | String(36) | NO | UUID hex, PK |
| session_id | String(36) | NO | FK → sessions.id, indexed |
| group_id | String(36) | NO | FK → groups.id, indexed |
| zip_path | String(500) | YES | Local path to built ZIP file |
| status | String(50) | NO | `pending` \| `ready` \| `error`; indexed |
| created_at | DateTime(tz) | NO | Indexed |
| completed_at | DateTime(tz) | YES | Set when status becomes `ready` or `error` |

---

### app_settings

| Column | Type | Nullable | Notes |
|---|---|---|---|
| key | String(100) | NO | PK — see App Settings Key Enum |
| value | Text | YES | Fernet-encrypted for sensitive keys |
| updated_at | DateTime(tz) | NO | |

---

## JSON Field Structures

### exif_json (assets table)

Stored as a JSON-serialized string. Keys the app reads:

```json
{
  "taken_at": "2024-06-15T14:32:00",
  "camera_make": "Apple",
  "camera_model": "iPhone 15 Pro",
  "gps_lat": 40.7128,
  "gps_lng": -74.0060,
  "iso": 64,
  "aperture": 1.78,
  "shutter_speed": "1/2000",
  "focal_length_mm": 24
}
```

`gps_lat` and `gps_lng` are also denormalized into the `assets` columns of the same name for indexed spatial queries.

---

### corrections_applied_json (edit_versions table)

```json
{
  "color": {
    "mode": "local",
    "lut": "Golden Hour v2",
    "temp_kelvin": 400,
    "saturation_delta": -8
  },
  "crop": {
    "mode": "ai",
    "x": 120,
    "y": 0,
    "w": 1800,
    "h": 2250,
    "rationale": "Rule of thirds, subject at upper-right intersection"
  },
  "removal": {
    "mode": "replicate",
    "model": "lama",
    "mask_path": "/data/masks/abc123.png"
  },
  "face": {
    "mode": "manual",
    "face_crop_id": "uuid-of-face-crop-row"
  }
}
```

Any sub-object may be `null` if that correction was not applied.

---

### bbox_json (face_crops table)

```json
{"x": 320, "y": 110, "w": 200, "h": 240}
```

All values are pixel coordinates relative to the full-resolution original. The face_recognition library returns `(top, right, bottom, left)` which is converted to `(x, y, w, h)` on write.

---

## SQLAlchemy Class → Table Mapping

| SQLAlchemy Class | Table Name |
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

---

## Encryption Policy

The following fields are Fernet-encrypted at rest using `cryptography.fernet.Fernet`:

| Table | Column |
|---|---|
| storage_credentials | refresh_token |
| storage_credentials | access_token |
| app_settings | value (sensitive keys only — see App Settings Key Enum) |

The Fernet key is loaded from the `FERNET_KEY` environment variable (stored in `.env`, never committed). Encrypt/decrypt pattern:

```python
from cryptography.fernet import Fernet

fernet = Fernet(settings.fernet_key.encode())

# Encrypt before writing
ciphertext: str = fernet.encrypt(plaintext.encode()).decode()

# Decrypt after reading
plaintext: str = fernet.decrypt(ciphertext.encode()).decode()
```

---

## Deletion Policy

| Table | On Resync | Never deleted |
|---|---|---|
| sessions | Previous session row marked `status="deleted"` | Row kept |
| assets | Hard-deleted for the wiped session | — |
| groups | Hard-deleted for the wiped session | — |
| group_assets | Hard-deleted (cascade from groups) | — |
| edit_versions | Hard-deleted (cascade from assets) | — |
| face_crops | Hard-deleted (cascade from assets) | — |
| descriptions | Hard-deleted (cascade from groups) | — |
| exports | Hard-deleted for the wiped session | — |
| cost_log | Never deleted | Always kept for billing audit |
| ai_cache | Never deleted | Shared across sessions |
| storage_credentials | Never deleted | Kept across resyncs |
| users | Never deleted | — |

Local disk files under `/data/` (previews, thumbnails, full-res copies, crops) are also wiped on resync for the previous session.

---

## cost_log Operation Enum Values

| Value | Description |
|---|---|
| `grouping_ai` | Claude Vision AI grouping refinement |
| `color_ai` | Claude Vision color adjustment suggestion |
| `crop_ai` | Claude Vision composition/crop suggestion |
| `object_removal` | Replicate LaMa inpainting |
| `face_retouch` | Replicate GFPGAN face enhancement |
| `nima` | Replicate NIMA aesthetic scoring |
| `description` | Claude caption generation |

---

## app_settings Key Enum

| Key | Sensitive (Fernet-encrypted) |
|---|---|
| `claude_api_key` | YES |
| `replicate_api_key` | YES |
| `google_client_id` | NO |
| `google_client_secret` | YES |
| `session_budget_usd` | NO |
| `session_hard_cap_usd` | NO |
| `style_seed` | NO |
