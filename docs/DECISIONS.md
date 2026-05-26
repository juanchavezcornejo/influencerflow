# DECISIONS.md

Append-only ADR log. One entry per decision that shapes the repo.
Never edit past entries — add a new entry that supersedes.

Format:
```
## {YYYY-MM-DD} — {Slug}

**Status:** accepted | superseded by <slug>
**Context:** why the question came up
**Decision:** what was chosen
**Consequences:** what this locks in / trades away
```

---

## 2026-04-16 — W0 toolchain

**Status:** accepted
**Context:** Starting Week 0 scaffolding. Needed to pick package managers,
license, and baseline stack versions.
**Decision:**
- **License:** proprietary (see `LICENSE`).
- **Python:** `uv` for dep management + venvs. `pyproject.toml` is the single
  source of truth.
- **Node:** `pnpm` 9.x via corepack. `packageManager` pinned in
  `web/package.json`.
- **Backend:** FastAPI 0.115+, SQLAlchemy 2.x async, Celery 5.4, Alembic 1.13.
- **Frontend:** Next.js 15 App Router, React 19, TypeScript strict +
  `noUncheckedIndexedAccess`, Tailwind v3.4 (shadcn/ui target), shadcn/ui.
- **DB:** Postgres 16.
- **Redis:** 7.
**Consequences:**
- Anyone running locally needs `uv`, `pnpm`, `docker compose` installed.
- Tailwind v4 migration is a future decision if shadcn moves default.
- CI uses `astral-sh/setup-uv@v3` and `pnpm/action-setup@v4`; don't re-add
  setup-python.

## 2026-04-16 — Scripts + slash commands over ad-hoc shell

**Status:** accepted
**Context:** To avoid re-discovering how to run/test/build each session.
**Decision:** All operational commands live in `scripts/*.sh`, mirrored by
`Makefile` targets and `.claude/commands/*.md` slash commands. Docs in
`docs/COMMANDS.md`.
**Consequences:**
- When adding a new operation, update `scripts/`, `Makefile`, and
  `docs/COMMANDS.md` together. Slash command is optional if the target is
  already trivially reachable via `make`.
- Don't run ad-hoc shell pipelines in the repo — add a script first.

## 2026-04-16 — Eager Celery in tests

**Status:** accepted
**Context:** Tests shouldn't require a running Redis broker.
**Decision:** `tests/conftest.py` sets `task_always_eager = True` as an
autouse fixture.
**Consequences:**
- `.delay().get()` works synchronously in tests.
- Task retry behavior is not exercised in unit tests — add integration tests
  later that run against a real broker.
