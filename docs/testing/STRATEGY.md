# STRATEGY.md — Test Strategy

What to test, where tests live, how to run them, and what to skip.

---

## Philosophy

- **Test behaviors, not implementations.** Tests should survive refactors. Avoid asserting on internal state; assert on observable outputs (HTTP responses, DB rows, return values).
- **Real Postgres preferred.** Integration tests use a real database. SQLite-in-memory is acceptable for pure service logic (e.g., `test_grouping_service.py`) but real Postgres is required for router tests and any query using Postgres-specific features.
- **Only mock paid external APIs.** Never mock the database, Redis (in integration tests), or local image processing libraries. Always mock Claude API and Replicate — they cost money and are unreliable in CI.
- **Celery runs eager.** The `_celery_eager_mode` autouse fixture makes all task calls synchronous. No broker needed in tests.

---

## API Tests

**Framework:** pytest with `pytest-asyncio`

**Configuration:** `api/pyproject.toml` under `[tool.pytest.ini_options]`

```toml
testpaths = ["tests"]
asyncio_mode = "auto"          # async tests need no @pytest.mark.asyncio decorator
addopts = "-q --strict-markers"
filterwarnings = ["ignore::DeprecationWarning"]
```

**Real Postgres via fixture:** Tests that need a database use an `AsyncSession` fixture that creates all tables, runs the test, then drops all tables. See `docs/testing/PATTERNS.md` for the full recipe.

**Celery eager mode:** The `_celery_eager_mode` autouse fixture in `conftest.py` sets `task_always_eager = True` and `task_eager_propagates = True` for every test, then restores the original values. No broker is needed.

**File naming convention:** `test_<module>.py` mirrors the source tree.

| Test file | Tests |
|---|---|
| `test_health.py` | `routers/health.py` |
| `test_grouping_service.py` | `services/grouping_service.py` |
| `test_phash.py` | `lib/phash.py` |
| `test_color_ops.py` | `lib/color_ops.py` |

**Kinds of tests:**

| Kind | Description |
|---|---|
| Unit | Pure functions in `lib/*`: deterministic, no I/O, fast. Use golden fixture images from `api/tests/fixtures/images/`. |
| Router | Use the `client` fixture (FastAPI `TestClient`). Assert on HTTP status + JSON body. |
| Service | Call the service directly with an injected `AsyncSession`. Mock integrations via constructor injection (pass a fake client). |
| Integration | Real Postgres required. Guard with `pytest.importorskip("asyncpg")` and skip gracefully if the DB is unreachable. |

---

## Frontend Tests

### TypeScript + ESLint as first line of defense

`pnpm typecheck` (`tsc --noEmit`) and `pnpm lint` (eslint) catch the majority of bugs before any test runs. These run in CI on every PR.

### Vitest for hooks and utils

When a hook or utility function needs a test (first instance: add `web/vitest.config.ts` and swap the placeholder `pnpm test` script). Use **Vitest + React Testing Library**.

Candidates for Vitest tests:
- Custom hooks in `web/src/hooks/`
- `lib/api-client.ts`
- `lib/cost-badge.tsx` logic

### Playwright E2E

Lands in W6 (ticket W6-004). Plan:
- Config: `web/playwright.config.ts`
- Tests: `web/e2e/`
- Runs against `docker compose up` with a mocked Google Drive adapter and fixture images; Replicate is also mocked.
- CI job `e2e` in `.github/workflows/ci.yml` is already scaffolded — adding `playwright.config.ts` activates it.

Smoke test flow (W6):
1. Log in.
2. Connect a mocked Google Drive folder (fixture images).
3. Resync.
4. Open a group.
5. Accept a local color correction.
6. Download the ZIP.
7. Assert ZIP is non-empty.

---

## CI Pipeline

Defined in `.github/workflows/ci.yml`. Three jobs:

| Job | Steps | Blocks merge? |
|---|---|---|
| `api` | `uv sync --extra dev` → ruff → mypy → pytest | Yes |
| `web` | `pnpm install` → eslint → `tsc --noEmit` → prettier --check → `pnpm test` | Yes |
| `e2e` | Playwright against docker-compose stack (skips if `playwright.config.ts` absent) | No (until W6) |

PRs are blocked on `api` and `web` jobs. The `e2e` job is informational until Playwright config lands.

---

## Coverage Targets

Coverage as a CI gate is deferred to Phase 2. During MVP, aim for:

| Layer | Target | Rationale |
|---|---|---|
| `lib/*` modules | 100% | Pure functions with golden fixtures; cheap to test, high value |
| Routers | Happy path + 404 per endpoint | Ensures wiring is correct; edge cases live in service tests |
| Services with branching logic | Fixture-driven test per branch | Grouping, editing, cost service all have meaningful branches |
| Integrations | Mocked client tests | Never hit real APIs in CI; verify request construction and response parsing |
| Celery tasks | Eager-mode smoke test per task | Validates task signature and DB side-effects |

---

## What NOT to Test

Skip tests for:

- **shadcn/ui components** — third-party primitives; tested upstream.
- **Generated migrations** in `api/alembic/versions/` — ruff excludes this directory; no unit tests needed.
- **`api/app/config.py`** — pydantic-settings wiring; trust the library.
- **`api/app/main.py` wiring** — FastAPI app factory; covered by router integration tests.
- **`pnpm test` placeholder** — the current `exit 0` script is intentional until Vitest config lands.

---

## Make Targets

```bash
make test        # run all tests (api + web)
make test-api    # pytest only
make test-web    # web typecheck + lint + unit tests
make lint        # non-mutating checks across both sides (ruff, mypy, eslint, prettier)
```
