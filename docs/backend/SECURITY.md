# Security

Auth, JWT, encryption, budget guards, and hardening conventions.

---

## Auth Flow

1. Frontend sends `POST /api/v1/auth/login` with `{email, password}`.
2. `UserRepository.get_by_email(email)` fetches the user row.
3. `bcrypt.checkpw(password, user.password_hash)` verifies the password.
4. `create_jwt_token(user.id)` mints a signed JWT (7-day expiry).
5. Token is returned in `AuthResponse.accessToken`.
6. Frontend includes the token in every subsequent request as `Authorization: Bearer <token>`.
7. Protected routes declare `current_user: User = Depends(get_current_user)`.
8. `get_current_user` (in `app/dependencies.py`) strips the `Bearer ` prefix, calls `decode_jwt_token(token)`, extracts `payload["user_id"]`, fetches the `User` row, and returns it. Raises `HTTPException(401)` at any failure point.

---

## JWT

**File:** `api/app/lib/jwt_utils.py`

| Property | Value |
|---|---|
| Signing algorithm | `HS256` |
| Payload fields | `user_id` (str), `iat` (datetime), `exp` (datetime) |
| Default expiry | 7 days from issuance |
| Secret source | `settings.jwt_secret` (env var `JWT_SECRET`) |

```python
def create_jwt_token(user_id: str, expires_in: timedelta = timedelta(days=7)) -> str:
    """Create a signed JWT token."""
    now = datetime.now(timezone.utc)
    payload = {"user_id": user_id, "iat": now, "exp": now + expires_in}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_jwt_token(token: str) -> dict | None:
    """Decode and validate a JWT token. Returns payload or None if invalid/expired."""
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.InvalidTokenError:
        return None
```

`decode_jwt_token` returns `None` (not raises) on any invalid or expired token. The caller (`get_current_user`) raises `HTTPException(401)` when it receives `None`.

---

## Single-User Model

InfluencerFlow is single-user in the MVP. Ownership is enforced at the router layer:

```python
session = await repo.get_by_id(session_id)
if not session or session.user_id != current_user.id:
    raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Session not found")
```

Returning `404` (not `403`) on ownership mismatch prevents information leakage — the caller cannot distinguish between "does not exist" and "belongs to someone else".

The single user is seeded from `settings.single_user_email` and `settings.single_user_password` during `make bootstrap`. These values come from the `.env` file, never from code defaults in production.

---

## Fernet Encryption

Sensitive fields (OAuth tokens, API keys stored in the database) are encrypted with Fernet symmetric encryption.

`settings.fernet_key` provides the key. Generate one with:

```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

Usage pattern:

```python
from cryptography.fernet import Fernet
from app.config import settings

_fernet = Fernet(settings.fernet_key.encode())

def encrypt(value: str) -> str:
    return _fernet.encrypt(value.encode()).decode()

def decrypt(value: str) -> str:
    return _fernet.decrypt(value.encode()).decode()
```

Fields encrypted at rest:
- `storage_credentials.access_token`
- `storage_credentials.refresh_token`
- Any third-party API keys stored in the DB

`fernet_key` must be a URL-safe base64-encoded 32-byte key. If the field is empty in settings, encryption is disabled (development only). In production (`settings.environment != "development"`), a missing `fernet_key` should raise at startup.

---

## Budget Guards

**File:** `api/app/services/budget_service.py`

Two configurable limits from `settings`:

| Setting | Default | Behavior |
|---|---|---|
| `session_budget_usd` | $10.00 | Soft cap — triggers a warning badge in the UI |
| `session_hard_cap_usd` | $50.00 | Hard cap — `allowed=False` blocks the AI operation |

`BudgetService.check_budget()` usage before any paid API call:

```python
from app.services.budget_service import BudgetService

budget = BudgetService(db)
check = await budget.check_budget(session_id, estimated_cost)

if not check["allowed"]:
    raise HTTPException(
        status_code=HTTPStatus.PAYMENT_REQUIRED,
        detail=f"Session hard cap ${check['hard_limit']:.2f} would be exceeded. "
               f"Current: ${check['current_spending']:.2f}",
    )

if check["exceeded_soft"]:
    # Surface warning to frontend via response header or response field
    pass  # still allowed, just warn

# Proceed with API call ...
# Then log cost immediately after
```

`check_budget()` return shape:

```python
{
    "allowed": bool,
    "exceeded_soft": bool,
    "exceeded_hard": bool,
    "current_spending": float,
    "soft_limit": float,
    "hard_limit": float,
    "remaining": float,
    "new_total": float,
}
```

---

## API Key Masking

When displaying API key values in logs or UI responses, mask all but the last 4 characters. Never log a full key.

Pattern to follow (implement in `app/lib/security_utils.py` or inline):

```python
def mask_key(key: str) -> str:
    """Return ****<last4> for display. Safe for empty/short strings."""
    if not key or len(key) <= 4:
        return "****"
    return f"****{key[-4:]}"
```

Usage:

```python
logger.info("google_drive token refreshed key=****%s", token[-4:])
```

Never pass raw tokens to `logger.info`, `logger.debug`, or any response body visible outside the service.

---

## Path Traversal Prevention

Any endpoint that writes to or reads from a path derived from user input must validate that the resolved path stays within the allowed data directory.

Pattern to follow (implement in `app/lib/security_utils.py` or inline):

```python
from pathlib import Path
from app.config import settings


def safe_path(user_input: str, base_dir: Path = settings.data_dir) -> Path:
    """
    Resolve user_input relative to base_dir and verify it does not escape.
    Raises ValueError on path traversal attempt.
    """
    resolved = (base_dir / user_input).resolve()
    if not str(resolved).startswith(str(base_dir.resolve())):
        raise ValueError(f"Path traversal attempt: {user_input!r}")
    return resolved
```

Apply `safe_path()` before any `open()`, `shutil.copy()`, or similar call that uses a path derived from request data (filenames, IDs embedded in paths, etc.).

---

## Rate Limiting

Global rate limiting is applied at the application level using `slowapi`.

| Scope | Limit |
|---|---|
| Default (all routes) | 200 requests / minute per IP |
| `POST /api/v1/auth/login` | 5 requests / 15 minutes per IP (configured in `routers/auth.py`) |

Setup in `app/main.py`:

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

Per-route override:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/login")
@limiter.limit("5/15 minutes")
async def login(request: Request, ...):
    ...
```

Rate limit responses return HTTP `429 Too Many Requests`.

---

## Phase 2 Notes

The following security concerns are deferred to Phase 2 (multi-user / public launch) and are **not** implemented in the MVP:

- **Multi-user isolation:** All DB queries will need `WHERE user_id = current_user.id` enforced at the repository layer (not just the router).
- **Row-level security (RLS):** Consider enabling PostgreSQL RLS policies as a second line of defense.
- **Token refresh:** `GoogleDriveClient` currently has a no-op stub when a 401 is received. Phase 2 requires automatic refresh using `refresh_token` and updating `storage_credentials`.
- **Fernet key rotation:** Add a key-versioning scheme so old tokens can be migrated without a downtime decryption pass.
- **CSRF:** NextAuth CSRF protection should be enabled for the credentials provider in Phase 2.
- **Data retention:** Define and implement a retention policy (auto-delete sessions + `/data/` files after N days).
- **Audit log:** Extend `cost_log` or add a separate `audit_log` table to track who accessed what and when.
- **Secrets manager:** Move `jwt_secret`, `fernet_key`, and API keys from `.env` to AWS Secrets Manager or Railway's secret store.
