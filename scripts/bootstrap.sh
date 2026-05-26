#!/usr/bin/env bash
# First-time setup: install API + web deps, copy .env files, prompt for credentials.
source "$(dirname "$0")/_lib.sh"

require uv pnpm

log "Installing API dependencies (uv sync)"
(cd api && uv sync --extra dev)

log "Installing web dependencies (pnpm install)"
(cd web && pnpm install)

# Copy .env.example → .env if not exists
for f in api/.env web/.env; do
  if [[ ! -f "$f" ]] && [[ -f "$f.example" ]]; then
    cp "$f.example" "$f"
  fi
done

# Run interactive credential setup
log "Setting up credentials..."
"$(dirname "$0")/setup-credentials.sh"

ok "Bootstrap complete! Next: make dev"
