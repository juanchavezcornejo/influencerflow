#!/usr/bin/env bash
# Generate a new Alembic revision with autogenerate.
#   Usage: scripts/migrate-new.sh "add users table"
source "$(dirname "$0")/_lib.sh"

require uv

[[ $# -ge 1 ]] || die "Usage: $0 \"<migration message>\""
msg="$*"

cd api
uv run alembic revision --autogenerate -m "$msg"
ok "Review the new file under api/alembic/versions/ before committing."
