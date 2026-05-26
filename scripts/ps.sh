#!/usr/bin/env bash
# Show docker-compose status + quick health probes.
source "$(dirname "$0")/_lib.sh"

require docker

log "docker compose ps"
docker compose ps

log "Health probes"
for url in "http://localhost:8000/api/v1/health" "http://localhost:3000/"; do
  code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 2 "$url" || echo "—")
  printf "  %s → %s\n" "$url" "$code"
done
