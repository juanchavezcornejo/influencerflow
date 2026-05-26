#!/usr/bin/env bash
# Start the full stack via docker-compose.
source "$(dirname "$0")/_lib.sh"

require docker

log "Starting full stack (postgres, redis, api, worker, web)"
exec docker compose up --build "$@"
