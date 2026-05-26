# COMMANDS.md

Every `scripts/*.sh`, every `make` target, and every `/slash` command in one
place. Keep this file in sync when adding new ones.

## Scripts

All live under `scripts/` and source `_lib.sh` for colors + strict mode.

| Script | Purpose |
|---|---|
| `bootstrap.sh` | First-time setup — `uv sync --extra dev` + `pnpm install` + copy `.env.example` → `.env`. |
| `dev.sh` | `docker compose up --build` — full stack. |
| `dev-api.sh` | Only `postgres + redis + api + worker`. For frontend-off sessions. |
| `dev-web.sh` | `pnpm dev` standalone. Assumes API is reachable at `API_BASE`. |
| `test.sh` | Runs `test-api.sh` + `test-web.sh`. |
| `test-api.sh` | `uv run pytest` in `api/`. |
| `test-web.sh` | `pnpm typecheck && pnpm lint && pnpm test` in `web/`. |
| `lint.sh` | Non-mutating: `ruff check`, `ruff format --check`, `mypy`, `eslint`, `tsc`, `prettier --check`. |
| `format.sh` | Mutating: `ruff format`, `ruff check --fix`, `prettier --write`. |
| `build.sh` | `pnpm build` + docker image builds for `api`, `worker`, `web`. |
| `clean.sh` | Remove `.venv`, `node_modules`, `.next`, all cache dirs. Keeps `./data`. |
| `clean-data.sh` | Wipe `./data` + `api/data`. Destructive, prompts. |
| `migrate.sh` | `uv run alembic upgrade head`. |
| `migrate-new.sh "msg"` | `uv run alembic revision --autogenerate -m "msg"`. |
| `reset-db.sh` | Drop + recreate `influencerflow` DB in the postgres container, then migrate. Destructive, prompts. |
| `logs.sh [svc]` | `docker compose logs -f --tail=200` — all services or one. |
| `shell-api.sh` | Python REPL inside the `api` container with `app`, `settings`, `AsyncSessionLocal` imported. |
| `ps.sh` | `docker compose ps` + curl health probes on `:8000` and `:3000`. |

## Makefile targets

Wrappers over the scripts. `make help` prints this list at runtime.

```
make bootstrap     First-time setup
make setup-credentials   Re-run credential setup (update .env files without re-installing deps)
make dev           Start full stack
make dev-api       API + worker + infra
make dev-web       Next.js standalone
make test          All tests
make test-api      Pytest only
make test-web      Web checks
make lint          Non-mutating checks
make format        Auto-format
make build         Production build
make clean         Remove caches
make clean-data    Wipe ./data (prompts)
make migrate       alembic upgrade head
make migrate-new msg="..."   New revision
make reset-db      Drop + recreate dev DB (prompts)
make logs [svc=api]          Tail compose logs
make shell-api     Python REPL in api container
make ps            compose ps + health probes
```

## Slash commands (Claude Code)

Project-scoped, live under `.claude/commands/`. Each is a small prompt Claude
executes when invoked as `/<name>`.

| Slash | Purpose |
|---|---|
| `/dev` | Start the stack (runs `make dev` for you). |
| `/test` | Run `make test` and summarize failures. |
| `/lint` | Run `make lint`, offer to `/format` if dirty. |
| `/format` | Run `make format`. |
| `/clean` | Confirm, then run `make clean`. |
| `/migrate "msg"` | `make migrate-new msg="..."` + review the generated diff. |
| `/ticket W1-005` | Load ticket from `docs/MVP_SPEC.md`, propose task breakdown + branch name. |
| `/ship` | Pre-PR checklist: lint + test + typecheck + diff summary. |
| `/status` | Current state: containers, last commit, uncommitted files, open tasks. |
| `/skill` | List available docs and when to consult each. |
