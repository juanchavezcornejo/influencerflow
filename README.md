# InfluencerFlow

Single-user web app that turns 100–1000 travel photos/videos into ready-to-post
Instagram content. Cost-conscious, non-destructive, low-res-first.

See [`CLAUDE.md`](./CLAUDE.md), [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md),
and [`docs/MVP_SPEC.md`](./docs/MVP_SPEC.md) for design.

---

## Repo layout

```
influencerflow/
├── api/                FastAPI backend + Celery workers
├── web/                Next.js 15 frontend
├── config/             Shared config (filename patterns, preview tiers)
├── docs/               Design docs
├── docker-compose.yml  Local dev orchestration
└── railway.toml        Railway services sketch
```

## Prerequisites

- **Docker** + **Docker Compose** (local dev)
- **Python 3.12** + [**uv**](https://github.com/astral-sh/uv)
- **Node 20+** + [**pnpm**](https://pnpm.io/) 9+
- Postgres 16, Redis 7 (provided by docker-compose)

## Quick start (local)

```bash
# 1. Start infra + services
docker compose up --build

# 2. (Alt) Run services manually
cd api && uv sync && uv run uvicorn app.main:app --reload
cd web && pnpm install && pnpm dev
```

- API: <http://localhost:8000/api/v1/health>
- Web: <http://localhost:3000>

## Environment

Copy `.env.example` files in `api/` and `web/` to `.env`. The minimal dev
defaults work out of the box with docker-compose.

## Tests

```bash
# API
cd api && uv run pytest && uv run ruff check . && uv run mypy app

# Web
cd web && pnpm lint && pnpm typecheck && pnpm test
```

## License

Proprietary. See [LICENSE](./LICENSE).
