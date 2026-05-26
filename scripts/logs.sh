#!/usr/bin/env bash
# Tail docker-compose logs. Optionally for one service.
#   Usage: scripts/logs.sh          # all services
#          scripts/logs.sh api      # just api
source "$(dirname "$0")/_lib.sh"

require docker

exec docker compose logs -f --tail=200 "$@"
