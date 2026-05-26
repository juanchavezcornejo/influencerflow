# DEVOPS.md — InfluencerFlow

Local development, Railway deployment, secrets, and operational runbooks.

---

## Local Development

### Docker Compose Services

| Service | Port | Purpose |
|---|---|---|
| `postgres` | 5432 | PostgreSQL 16 — primary database |
| `redis` | 6379 | Celery broker + result backend + pub/sub for SSE progress events |
| `api` | 8000 | FastAPI on uvicorn with `--reload` (hot-reload on file changes) |
| `worker` | — | Celery worker consuming the `default` queue (no external port) |
| `web` | 3000 | Next.js dev server (`pnpm dev`) |

### Named Volumes

| Volume | Mounted at | Purpose |
|---|---|---|
| `postgres_data` | Postgres data dir | DB persistence across container restarts |
| `data` | `/data` on `api` + `worker` | Downloaded originals, previews, edits, exports |
| `web_node_modules` | `/app/node_modules` | Isolates pnpm store from host |
| `web_next` | `/app/.next` | Next.js build artifacts — avoids rebuild on every restart |

---

## Make Targets

Full catalog — every target delegates to a matching script under `scripts/`.

| Target | What it does |
|---|---|
| `make help` | List all targets with descriptions |
| `make bootstrap` | First-time setup: `uv sync` + `pnpm install` + writes `.env` files |
| `make setup-credentials` | Re-run credential setup to update `.env` files |
| `make dev` | `docker compose up --build` — full stack |
| `make dev-api` | Start `api` + `worker` + infra only (no `web`) |
| `make dev-web` | Start Next.js dev server standalone |
| `make test` | Run all tests (api + web) |
| `make test-api` | pytest only |
| `make test-web` | Web typecheck + lint + unit tests |
| `make lint` | Non-mutating checks: ruff, mypy, eslint, prettier --check |
| `make format` | Auto-format and auto-fix: ruff format, ruff --fix, prettier --write |
| `make build` | Production build: `next build` + docker build |
| `make clean` | Remove build/install caches — keeps `./data` intact |
| `make clean-data` | Wipe `./data` volume (prompts for confirmation) |
| `make migrate` | `alembic upgrade head` |
| `make migrate-new msg="..."` | `alembic revision --autogenerate -m "msg"` |
| `make reset-db` | Drop + recreate dev DB, then migrate (prompts for confirmation) |
| `make logs [svc=api]` | Tail `docker compose logs` — omit `svc` for all services |
| `make shell-api` | Python REPL inside the running `api` container |
| `make ps` | `docker compose ps` + health probes |

---

## First-Time Setup

```bash
make bootstrap   # uv sync + pnpm install + writes api/.env and web/.env
make dev         # docker compose up --build
```

Verify:
- Frontend: http://localhost:3000
- API docs: http://localhost:8000/api/v1/docs
- Readiness probe: http://localhost:8000/api/v1/health/ready

If the readiness probe fails, check `make ps` and `make logs svc=api`.

---

## Railway Deployment

### Services

| Service | Source dir | Start command |
|---|---|---|
| `api` | `api/` | `uv run alembic upgrade head && uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| `worker` | `api/` | `uv run celery -A app.workers.celery_app worker -Q default,sync,preview,ai,edit,export --concurrency=2 -l info` |
| `web` | `web/` | `pnpm build && pnpm start` |
| `postgres` | Plugin | Managed by Railway |
| `redis` | Plugin | Managed by Railway |

### Volume

A single Railway volume named `data` (20 GB for MVP) is mounted at `/data` on both `api` and `worker`. Both services share the same physical volume so downloaded assets written by the worker are readable by the API.

### Healthcheck Paths

| Path | Purpose |
|---|---|
| `GET /api/v1/health` | Liveness — always returns 200 if process is up |
| `GET /api/v1/health/ready` | Readiness — checks DB, Redis, and `/data` volume |

External traffic reaches the app through the `web` service only. Next.js rewrites `/api/v1/*` to the internal `api` service via Railway's private network. The `api` service has no separate public domain.

---

## First Deploy Checklist

1. **Push code** — connect Railway project to the GitHub repo; Railway auto-deploys on push to `main`.
2. **Set env vars** — copy every variable from `api/.env.example` into the `api` and `worker` service configs; copy `web/.env.example` into the `web` service config.
3. **Provision Postgres + Redis** — add the Railway Postgres and Redis plugins; they inject `DATABASE_URL` and `REDIS_URL` automatically.
4. **Run migrations** — the `api` start command runs `alembic upgrade head` before uvicorn starts; confirm in the deploy log.
5. **Create seed user** — exec into the `api` container and run the seed script: `uv run python -m app.scripts.seed_user`.
6. **Smoke test** — `GET https://<your-domain>/api/v1/health/ready` must return `{"status": "ok"}`.

---

## Rotating Secrets

### General procedure

1. Generate the new value locally.
2. Update the Railway env var on the affected service(s).
3. Redeploy the service.

### FERNET_KEY rotation

Fernet is used to encrypt Google OAuth refresh tokens at rest. Hot-swapping the key would make all existing ciphertexts unreadable.

Safe rotation procedure:

1. Generate the new key: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
2. Add the new key as `FERNET_KEY_NEW` in Railway; keep `FERNET_KEY` (old) in place.
3. Deploy a one-time migration script that re-encrypts every `storage_credentials.refresh_token` from old key → new key.
4. After successful re-encryption, rename `FERNET_KEY_NEW` → `FERNET_KEY` and remove the old value.
5. Redeploy all services.

Never remove `FERNET_KEY` (old) before re-encryption is confirmed — doing so locks out all Drive-connected users.

---

## Logs and Debugging

### Local

```bash
make logs             # all services
make logs svc=api     # api only
make logs svc=worker  # celery worker only
```

### Structured logs

All services emit structured JSON logs via `structlog`. Key fields:

| Field | Description |
|---|---|
| `timestamp` | ISO 8601 UTC |
| `level` | `info` / `warning` / `error` |
| `service` | `api` or `worker` |
| `trace_id` | UUID propagated from HTTP request through Celery task |
| `session_id` | When a session is in scope |
| `message` | Human-readable line |

To trace a slow sync end-to-end, filter by `trace_id`:

```bash
# In Railway log viewer, filter by: trace_id=<uuid>
```

The `trace_id` is set by the API on each inbound request and forwarded as a Celery task header so worker logs are correlated with the originating HTTP call.

---

## Disk Management

| Context | Command |
|---|---|
| Local — wipe `./data` | `make clean-data` (prompts before deleting) |
| Railway — manual cleanup | SSH into `api` container, then `rm -rf /data/previews/*` |

### Per-session cleanup on Resync

When a user triggers Resync, the backend calls `shutil.rmtree` on `/data/<session_id>/` before downloading fresh assets. A strict path check prevents accidentally wiping anything outside the session directory.

### Railway volume limits

Monitor volume usage in the Railway service metrics dashboard. Alert threshold: 80% of the provisioned 20 GB. If you approach the limit, run manual cleanup or increase the Railway volume size.

---

## Troubleshooting

| Problem | Likely cause | Fix |
|---|---|---|
| DB connection refused | Postgres container not healthy, wrong `DATABASE_URL` | Run `make ps` to check container health; verify `DATABASE_URL` includes `+asyncpg` driver |
| Redis timeout | Redis container not running, wrong `REDIS_URL` | `make ps`, check Redis health; verify `REDIS_URL` scheme is `redis://` |
| Preview not generated | Worker not running, `DATA_DIR` path wrong, `data` volume not mounted | Check `make logs svc=worker`; ensure both `api` and `worker` mount the `data` volume at `/data` |
| Worker tasks not running | `CELERY_TASK_ALWAYS_EAGER` left `True` in production config, broker unreachable | Verify `REDIS_URL` is reachable from worker; check that `task_always_eager` is not set outside tests |
