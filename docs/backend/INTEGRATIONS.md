# External Integrations

Claude API, Replicate, and Google Drive client conventions.

---

## ClaudeClient

**File:** `api/app/integrations/claude.py`

### Constructor

```python
ClaudeClient(cache_repo=None)
```

- `cache_repo`: optional repository object exposing `get(cache_key)` / `set(cache_key, result, ...)`. When provided, responses are cached by SHA256 key before the API is called.
- Internally creates an `anthropic.Anthropic` instance using `settings.anthropic_api_key`.

### Method Signatures

```python
async def call(
    self,
    prompt_name: str,       # e.g. "OBJECT_REMOVAL_V1"
    prompt_version: str,    # version string for cache-key scoping
    variables: dict[str, Any],   # must include "prompt_text" key for text content
    model: str = "claude-opus-4-7",
    vision_content: list | None = None,  # list of Anthropic image content objects
) -> dict:
    """
    Returns:
        {
          "text": str,           # response text
          "model": str,
          "tokens_in": int,
          "tokens_out": int,
          "cache_key": str,
        }
    On error:
        {
          "error": str,
          "model": str,
          "cache_key": str,
        }
    """
```

### Caching Behavior

Cache key is SHA256 of `{prompt_name, prompt_version, variables, len(vision_content)}` (sorted JSON). The count of vision images is hashed — not the image bytes — so identical text calls with the same number of images hit the cache.

Cache lookup happens **before** every API call. On a hit, the raw cached dict is returned immediately. On a miss, the API is called and the result is stored via `cache_repo.set()`.

### Model Selection Rule

Default model is `claude-opus-4-7`. Pass `model=` explicitly to use a cheaper model (e.g. Haiku) for high-volume, low-complexity calls such as duplicate detection or caption suggestions on thumbnails. Confirm with the user before using Opus for bulk operations.

---

## ReplicateClient

**File:** `api/app/integrations/replicate.py`

### Constructor

```python
ReplicateClient(cache_repo=None)
```

- `api_token` is read from `settings.replicate_api_key`.
- `base_url = "https://api.replicate.com/v1"`.
- Concurrency is limited to **3 simultaneous requests** via `asyncio.Semaphore(3)`.

### Method Signatures

```python
async def run(
    self,
    model: str,                              # Replicate version ID
    inputs: dict[str, Any],                  # model-specific input dict
    webhook_events_filter: list[str] | None = None,
) -> dict:
    """
    Returns on success:
        {"output": Any, "status": "success", "model": str, "prediction_id": str}
    Returns on failure/timeout:
        {"error": str, "status": "failed"|"canceled"|"timeout"|"error", ...}
    """
```

### Polling Behavior

`run()` calls `_create_and_poll_prediction()`:

1. `POST /v1/predictions` with `{"version": model, "input": inputs}`.
2. Polls `GET /v1/predictions/{id}` every **2 seconds**.
3. Returns when status is `succeeded`, `failed`, or `canceled`.
4. Hard timeout: **600 seconds** (10 minutes). Returns `{"error": "Prediction timeout"}` on expiry.
5. Uses `asyncio.Semaphore(3)` to cap concurrent in-flight requests.

---

## GoogleDriveClient

**File:** `api/app/integrations/google_drive.py`

### Constructor

```python
GoogleDriveClient(access_token: str, refresh_token: str | None = None)
```

- Builds a `googleapiclient.discovery.Resource` ("drive", "v3") using the access token.
- Concurrency is limited to **1 request at a time** via `asyncio.Semaphore(1)` to respect Drive rate limits.

### Method Signatures

```python
async def list_folder_recursive(
    self,
    folder_id: str,
    page_size: int = 100,
) -> list[dict[str, Any]]:
    """
    List all files (and subfolders) recursively.
    Each item: {id, name, mimeType, createdTime, modifiedTime, fileSize}.
    Subfolder items are expanded in-place (depth-first).
    """

async def download_file(self, file_id: str, dest_path: str) -> None:
    """
    Download file content to dest_path using MediaIoBaseDownload.
    Raises googleapiclient.errors.HttpError on API errors.
    """

async def get_folder_metadata(self, folder_id: str) -> dict[str, Any]:
    """
    Returns: {id, name, file_count (bool approximation for MVP)}.
    """
```

### OAuth helper (GoogleDriveOAuth)

```python
GoogleDriveOAuth.get_auth_url() -> str          # returns OAuth consent URL
GoogleDriveOAuth.exchange_code_for_tokens(code: str) -> dict  # {refresh_token, access_token, token_expiry}
```

`secrets/google_oauth.json` must be created by the developer (not committed). See `scripts/setup-credentials.sh`.

---

## Cost Logging Contract

Every paid API call (Claude or Replicate) **must** log to `cost_log` immediately after a successful response. This is not optional — it feeds the budget guard and the session cost breakdown UI.

```python
from app.repositories.cost_log import CostLogRepository

# After a Claude call:
cost_repo = CostLogRepository(db)
await cost_repo.create(
    session_id=session_id,
    operation="ai_grouping",          # human-readable operation name
    model=result["model"],
    tokens_in=result["tokens_in"],
    tokens_out=result["tokens_out"],
    dollars_estimate=_estimate_dollars(result["tokens_in"], result["tokens_out"]),
)
await db.commit()

# After a Replicate call:
await cost_repo.create(
    session_id=session_id,
    operation="object_removal",
    model=model_version_id,
    tokens_in=None,
    tokens_out=None,
    dollars_estimate=REPLICATE_LAMA_COST_PER_RUN,  # constant from config
)
await db.commit()
```

`CostLogRepository.create()` signature:

```python
async def create(
    self,
    session_id: str,
    operation: str,
    model: str | None = None,
    tokens_in: int | None = None,
    tokens_out: int | None = None,
    dollars_estimate: float | None = None,
) -> CostLog
```

---

## Error Handling

| Integration | Error type | Handling |
|---|---|---|
| ClaudeClient | `anthropic.APIError` (any) | Caught inside `call()`. Returns `{"error": str(e), "model": ..., "cache_key": ...}`. Caller checks for `"error"` key. |
| ClaudeClient | Missing `anthropic_api_key` | Raised at `Anthropic()` construction. Will surface as a 500 if not caught. Guard with `BudgetService.check()` before calling. |
| ReplicateClient | `httpx.HTTPStatusError` | Caught inside `_create_and_poll_prediction()`. Returns `{"error": str(e), "status": "error"}`. |
| ReplicateClient | Timeout > 600s | Returns `{"error": "Prediction timeout", "status": "timeout"}`. |
| ReplicateClient | `status == "failed"` | Returns `{"error": prediction["error"], "status": "failed"}`. |
| GoogleDriveClient | `HttpError` status 401 | Raised after no-op token-refresh stub (MVP). Caller must handle and surface as 401. |
| GoogleDriveClient | `HttpError` other | Re-raised. Router should catch and return 502. |

---

## Adding a New Integration

1. Create `api/app/integrations/<name>.py`.
2. Define a client class. Constructor reads credentials from `settings` only — never `os.environ` directly.
3. Add credential fields to `Settings` in `api/app/config.py` with empty-string defaults.
4. Populate the fields in `.env` and `scripts/setup-credentials.sh`.
5. Add a `cache_repo` parameter if the integration can return cacheable results.
6. Every paid call must call `CostLogRepository.create()` immediately after success.
7. Return a plain dict (not a model object) so callers can inspect `"error"` key without exceptions.
8. Add integration to the relevant service or task file — never call integration clients directly from routers.
