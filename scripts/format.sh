#!/usr/bin/env bash
# Auto-format + auto-fix lint for api + web.
source "$(dirname "$0")/_lib.sh"

require uv pnpm

log "API: ruff format"
(cd api && uv run ruff format .)

log "API: ruff check --fix"
(cd api && uv run ruff check --fix .)

log "Web: prettier --write"
(cd web && pnpm format)

ok "Formatted"
