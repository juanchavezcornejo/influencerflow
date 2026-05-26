#!/usr/bin/env bash
# Non-mutating checks: lint + format check + typecheck for api + web.
source "$(dirname "$0")/_lib.sh"

require uv pnpm

log "API: ruff check"
(cd api && uv run ruff check .)

log "API: ruff format --check"
(cd api && uv run ruff format --check .)

log "API: mypy"
(cd api && uv run mypy app)

log "Web: eslint"
(cd web && pnpm lint)

log "Web: tsc --noEmit"
(cd web && pnpm typecheck)

log "Web: prettier --check"
(cd web && pnpm format:check)

ok "Lint clean"
