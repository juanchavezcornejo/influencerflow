#!/usr/bin/env bash
# Drop + recreate the dev DB and re-run migrations.
# Assumes postgres is running via docker-compose with the dev credentials.
source "$(dirname "$0")/_lib.sh"

require docker uv

printf "%sThis will DROP DATABASE influencerflow.%s\n" "$C_BOLD" "$C_RESET"
read -r -p "Continue? [y/N] " reply
[[ "$reply" =~ ^[Yy]$ ]] || die "Aborted"

log "Dropping + recreating database"
docker compose exec -T postgres psql -U postgres -d postgres -v ON_ERROR_STOP=1 <<'SQL'
DROP DATABASE IF EXISTS influencerflow;
CREATE DATABASE influencerflow;
SQL

log "Running migrations"
(cd api && uv run alembic upgrade head)

ok "DB reset complete"
