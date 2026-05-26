#!/usr/bin/env bash
# Run Next.js dev server outside docker. Assumes API is reachable at API_BASE.
source "$(dirname "$0")/_lib.sh"

require pnpm

log "Starting Next.js dev server (pnpm dev)"
cd web
exec pnpm dev "$@"
