#!/usr/bin/env bash
# Production build: Next.js + docker images.
source "$(dirname "$0")/_lib.sh"

require pnpm docker

log "Building web (pnpm build)"
(cd web && pnpm build)

log "Building docker images (api + web)"
docker compose build api worker web

ok "Build complete"
