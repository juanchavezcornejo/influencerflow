# Product Flow

> Read this before building any user-facing feature. It describes what happens at each step and what data each step produces.

## 10-Step User Flow

### Step 1 — Resync
User pastes a Google Drive folder URL → clicks **Resync**.
Backend wipes workspace (DB rows + local previews + temp files for the session),
lists files in the folder, enqueues `tasks_sync.download_and_preview` for each asset.
Session status: `pending` → `syncing` → `ready` (or `error`).

### Step 2 — Deterministic Grouping (free, automatic)
Runs automatically after all assets have previews. `tasks_sync.run_deterministic_grouping`.
Logic (applied in order):
1. Parse filename via `config/filename_patterns.yaml`.
2. Group by EXIF `DateTimeOriginal` — same calendar day = same candidate group.
3. Split group if time gap between consecutive shots > 2 hours.
4. Split group if GPS distance between consecutive shots > 500 m.
Result: `groups` + `group_assets` rows created; assets remain in `grouped` status.

### Step 3 — AI Grouping Refinement (🤖 opt-in, paid)
User clicks **AI Group** per cluster or globally.
UI shows cost estimate → user confirms → tile-packed thumbnails sent to Claude Vision →
Claude returns suggested group boundaries → user accepts/rejects each suggestion.
Prompt: `GROUPING_REFINEMENT_V1` in `docs/PROMPTS.md`.

### Step 4 — Labeling within Group (automatic after grouping)
- `is_near_duplicate`: pHash (free, local) — threshold in `config/filename_patterns.yaml`.
- `aesthetic_score`: Replicate NIMA (💰 opt-in per group).
- `has_face`: `face_recognition` HOG model (free, local).
- `is_video`: EXIF / file extension.

### Step 5 — Review Grid
Frontend `/session/{id}`: groups displayed as cards, assets as thumbnails.
Near-duplicates collapsed (worst-scored hidden, best shown). Score + face + video badges visible.
User can: quick-reject an asset, drag asset between groups, expand near-dup cluster.

### Step 6 — Edit View
Frontend `/edit/{assetId}`: full-screen before/after slider.
Four correction tabs — Color, Crop, Remove, Face — each with three modes:
- **Manual**: user uploads a corrected image.
- **Local/free**: Pillow color ops, SmartCrop (no API call).
- **AI**: Claude suggests parameters → Replicate executes (💰 confirm required).
Every accepted correction creates a new `edit_versions` row.

### Step 7 — Face Retouch
1. Backend detects face bbox in full-res original (`face_detect.py`).
2. Crop + 20% padding → user downloads.
3. User edits externally → re-uploads via `POST /face-crops/{id}/upload`.
4. Backend aligns via dlib/mediapipe landmarks → `blend.py` Poisson seamless clone.
5. Output replaces face region in full-res working copy.

### Step 8 — Edit History
Each accepted correction: new `edit_versions` row (parent chain preserved).
Reject: marks `user_decision = "rejected"`, creates new branch from parent version.
Regenerate: re-runs the AI step, costs tokens, requires confirmation dialog.

### Step 9 — Description Generation (🤖 paid)
User clicks **Generate** in DescriptionPanel.
Backend tile-packs preview images for the group + EXIF + style seed + custom prompt →
sends to Claude Sonnet → returns caption in user's voice.
Result stored in `descriptions` table; user can regenerate (new row) or set one as current.

### Step 10 — Export
User clicks **Download ZIP** in ExportPanel.
Backend enqueues `tasks_export.build_zip`; Celery builds ZIP with full-res assets
named `01_place.jpg`, `02_place.jpg`, etc.; SSE broadcasts progress.
ZIP download via HMAC-signed URL (`GET /exports/{id}/download`).
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
any state ──(user rejects)──► rejected
```

## Cost Gates — Requires Confirm Dialog Before Executing

| Operation | UI trigger | Estimated cost |
|---|---|---|
| AI grouping refinement | "AI Group" button | $0.10–0.30 / session |
| Aesthetic scoring (NIMA) | "Score" button per group | ~$0.01 / asset |
| Color AI suggestion | Mode = AI in Color tab | ~$0.05 / asset |
| Object removal | Remove tab, AI or API mode | ~$0.01 / asset |
| Face enhancement (GFPGAN) | Face tab, Local/API mode | ~$0.005 / asset |
| Description generation | "Generate" button | ~$0.02 / post |

Free (no dialog): preview generation, deterministic grouping, pHash, local face detection, local color ops, manual upload.

## Resync Behavior (Wipe Order)

On resync, in this exact order:
1. Hard-delete: `edit_versions`, `face_crops`, `descriptions`, `group_assets`, `groups`, `assets` for the session.
2. Hard-delete: `exports` for the session.
3. **Keep**: `cost_log` entries (audit trail, never deleted).
4. **Keep**: `ai_cache` entries (prompt cache, never deleted).
5. Remove local preview files and temp files for the session from disk.
6. Reset session status to `pending`.
7. Fresh download + preview + grouping cycle begins.

## Non-Goals (MVP)

- No direct Instagram posting — copy-paste only.
- No automated video editing — manual round-trip only.
- No AI face retouching — GFPGAN only (user uploads the edit, no Claude suggestions).
- No multi-user support.
- No style learning from past posts (V1 feature).
