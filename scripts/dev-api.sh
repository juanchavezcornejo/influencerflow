#!/usr/bin/env bash
# API + worker + infra, no web. Use when you're iterating on backend only.
source "$(dirname "$0")/_lib.sh"

require docker

log "Starting API stack (postgres, redis, api, worker)"
exec docker compose up --build postgres redis api worker "$@"
