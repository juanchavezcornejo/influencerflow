# Processing Pipeline

End-to-end asset pipeline from cloud storage to export ZIP.

---

## Full Pipeline

```
Google Drive folder
        │
        ▼  GoogleDriveClient.list_folder_recursive()
  List all files
        │
        ▼  GoogleDriveClient.download_file()
  Download to /data/temp/{session_id}/{filename}
        │
        ├─── is_video? ──────────────────────────────────┐
        │                                                │
        ▼  lib/preview.generate()                        │ (skipped for video in MVP)
  Generate thumbnail (384px) + preview (1024px)         │
        │                                                │
        ▼  lib/exif.extract_exif()                       │
  Extract EXIF (datetime, GPS, camera, ISO, …)          │
        │                                                │
        ▼  lib/phash.compute_phash()                     │
  Compute perceptual hash from thumbnail                │
        │                                                │
        ▼  lib/face_detect.detect_faces()                │
  Detect faces (HOG model, local)                       │
        │                                                │
        ├─────────────────────────────────────────────────┘
        ▼  GroupingService.regroup_deterministic()
  Group by time gap (>2h) + GPS distance (>500m)
        │  lib/phash.hamming_distance() for near-dupe clustering
        │
        ▼  Review UI (user approves/rejects)
  Edit view — color / object removal / crop / face
        │
        ├─── tasks_editing.apply_corrections_full_res
        │    lib/color_ops.apply_corrections()
        │
        ├─── face: lib/blend.blend_face()
        │
        ▼  tasks_export.build_zip
  Export ZIP → /data/exports/{session_id}/{group_id}.zip
```

---

## File Storage Layout

All ephemeral data lives under the Railway volume at `/data/`. Originals on Google Drive are never modified.

```
/data/
├── temp/
│   └── {session_id}/
│       └── {original_filename}         # downloaded original (full-res)
├── previews/
│   └── {asset_stem}_thumbnail.jpg      # 384px, EXIF stripped
│   └── {asset_stem}_preview.jpg        # 1024px, EXIF retained
│   └── {asset_stem}_hi_preview.jpg     # 1536px (opt-in)
├── edits/
│   └── {asset_id}/
│       └── {edit_version_id}.jpg       # output of each accepted edit
├── exports/
│   └── {session_id}/
│       └── {group_id}.zip              # final download ZIPs
└── temp_exports/
    └── {group_id}/                     # staging dir before ZIP (auto-cleaned)
        └── 01_{place_or_date}.jpg
        └── 02_{place_or_date}.jpg
```

---

## Preview Tiers

Configured in `api/app/lib/preview.py` (`PREVIEW_TIERS` dict), mirroring `web/src/config/preview.config.ts`.

| Tier key | Longest side | JPEG quality | EXIF | Use case |
|---|---|---|---|---|
| `thumbnail` | 384px | 85 | Stripped | UI grid, pHash, face detect |
| `preview` | 1024px | 85 | Retained | AI grouping, AI labeling, description generation |
| `hi_preview` | 1536px | 85 | Retained | Detailed composition analysis (opt-in) |
| original | full resolution | — | Retained | Final export only, never modified |

Aspect ratio is always preserved. The longest side is capped at the tier limit; the shorter side scales proportionally. Resize uses `Image.Resampling.LANCZOS`.

---

## lib/ Function Signatures

Signatures are as they exist in the source. All functions are synchronous and CPU-bound; they are called via `run_in_executor` from async contexts.

### lib/preview.py

```python
def generate(source_path: str, tier: str = "preview", dest_path: str | None = None) -> str:
    """
    Generate a preview image at a given tier.
    Returns path to the generated JPEG.
    Raises FileNotFoundError if source missing; ValueError for unknown tier or corrupt image.
    """
```

### lib/exif.py

```python
def extract_exif(image_path: str) -> dict:
    """
    Extract EXIF data from an image.
    Returns dict with keys:
        datetime_original, gps_lat, gps_lng, camera, lens, iso, aperture, shutter.
    All values may be None if not present in EXIF.
    Uses piexif as primary parser, PIL ExifTags as fallback.
    """
```

### lib/phash.py

```python
def compute_phash(image_path: str, hash_size: int = 8) -> str:
    """
    Compute perceptual hash of an image.
    Returns 64-bit hash as a hex string (hash_size=8 → 16-char hex).
    Raises FileNotFoundError if image missing.
    """

def hamming_distance(hash1: str, hash2: str) -> int:
    """
    Compute Hamming distance between two hex hash strings.
    Raises ValueError if hashes differ in length.
    """
```

GroupingService uses `PHASH_HAMMING_THRESHOLD = 5` — assets with distance < 5 are considered near-duplicates.

### lib/face_detect.py

```python
def detect_faces(image_path: str) -> list[dict]:
    """
    Detect faces using HOG model (face_recognition library, local, no network).
    Returns list of dicts: {top, right, bottom, left, confidence}.
    confidence is always 1.0 (HOG does not produce a score).
    Raises FileNotFoundError / ValueError on bad input.
    """

def has_faces(image_path: str) -> bool:
    """
    Convenience wrapper. Returns True if any faces detected; False on any error.
    """
```

### lib/tile_pack.py

```python
def pack_thumbnails(thumbnail_paths: list[str], cols: int = 3, padding: int = 8) -> bytes:
    """
    Pack thumbnails into a grid image for Claude Vision batch calls.
    Returns PNG bytes. Returns b"" on empty input or all-invalid images.
    Tiles are numbered 1-N in the top-left corner.
    """

def hash_pack_input(thumbnail_paths: list[str], cols: int, padding: int) -> str:
    """
    Generate deterministic SHA256 hash of packing inputs (for caching).
    """
```

### lib/color_ops.py

```python
def apply_exposure(image: Image.Image, exposure: float) -> Image.Image: ...
def apply_contrast(image: Image.Image, contrast: float) -> Image.Image: ...
def apply_saturation(image: Image.Image, saturation: float) -> Image.Image: ...
def apply_white_balance(image: Image.Image, temp: float = 0, tint: float = 0) -> Image.Image: ...
def apply_highlights_shadows(image: Image.Image, highlights: float = 0, shadows: float = 0) -> Image.Image: ...

def apply_corrections(image: Image.Image, corrections: dict[str, Any]) -> Image.Image:
    """
    Apply all corrections in order:
        exposure → contrast → saturation → white_balance → highlights/shadows
    corrections dict keys are optional; omitted keys are skipped.
    """

def apply_lut(image: Image.Image, lut_path: str) -> Image.Image:
    """
    Apply a named LUT preset. Supported names: 'golden', 'neutral', 'moody'.
    Falls back to identity if colour-science is not installed.
    """
```

All `apply_*` functions return a new `Image.Image`; the input is never mutated.
Numeric params use 0 as identity (no change). Range is typically -1.0 to +1.0 (or -50 to +50 for white balance temp/tint).

### lib/blend.py

```python
def blend_face(
    original_path: str,
    crop_path: str,
    user_crop_path: str,
    landmarks: list | None,
    output_path: str,
) -> bool:
    """
    Blend user-edited face crop back into original image.
    Uses landmark-based elliptical mask when landmarks provided; falls back to simple alpha mask.
    Returns True on success, False on any failure.
    """
```

---

## Non-Destructive Rule

Originals stored on Google Drive are never touched. The local copy downloaded to `/data/temp/{session_id}/` is read-only input for preview generation.

Every edit produces a **new file** in `/data/edits/{asset_id}/{edit_version_id}.jpg`. The `edit_versions` table tracks each version; the router or service chooses which version is current. Rejecting a version simply marks it `user_decision = "rejected"` in the DB — no file is deleted.

The version-0 entry (`corrections_applied_json = {"preset": "original"}`, `changes_log_text = "- Original (unedited)"`) is written during sync to represent the unedited state.

---

## Celery Task Chain for Sync

The sync pipeline runs as a single Celery task (`tasks_sync.resync_session`) rather than a chain, because it must operate sequentially on each asset (download → preview → EXIF → phash → face → DB write) before moving to the next file. Parallelism within a session is not implemented in the MVP.

The task uses the `asyncio.run()` pattern to drive an async inner function from a synchronous Celery task context:

```python
@celery_app.task(bind=True, name="tasks_sync.resync_session")
def resync_session(self, session_id: str) -> dict:
    async def _resync() -> None:
        async with AsyncSessionLocal() as db:
            # ... all async work ...
    asyncio.run(_resync())
    return {"session_id": session_id, "status": "complete"}
```

Steps inside `_resync()`:
1. Transition session status to `"syncing"`.
2. Fetch `StorageCredentials` for the session owner.
3. Wipe existing asset rows via `AssetRepository.delete_by_session()`.
4. `GoogleDriveClient.list_folder_recursive()` — enumerate all files.
5. For each file: download → generate thumbnail + preview → extract EXIF → compute pHash → detect faces → write asset row + edit_version_0.
6. `GroupingService.regroup_deterministic()` — cluster by time gap + GPS.
7. Transition session status to `"ready"`.
8. On any exception: transition to `"error"`.

---

## Export ZIP Structure

`tasks_export.build_zip(group_id)` assembles the ZIP in a temporary staging directory before archiving:

```
{group_id}.zip
├── 01_{place_or_date}.jpg    # position 1, accepted edit or original
├── 02_{place_or_date}.jpg
└── ...
```

Naming rule per file:
- Position prefix: two-digit zero-padded index (`01`, `02`, …).
- Suffix: `location` field from EXIF JSON (first 20 chars, spaces → underscores, lowercased) if present; otherwise `taken_at` formatted as `YYYYMMDD`; otherwise `unknown`.
- Extension: inherited from the source file's extension.

Source priority per asset:
1. Most recent `edit_versions` row with `user_decision = "accepted"` and a non-null `output_path`.
2. `asset.full_res_local_path` (original download).
3. Asset is skipped if neither exists.

ZIP is written to `/data/exports/{session_id}/{group_id}.zip`. The staging directory is deleted after archiving.
