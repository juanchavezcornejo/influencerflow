#!/usr/bin/env bash
# Apply Alembic migrations to the currently-configured DB.
source "$(dirname "$0")/_lib.sh"

require uv

cd api
exec uv run alembic upgrade head "$@"
