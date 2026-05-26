#!/usr/bin/env bash
# Pytest for the API.
source "$(dirname "$0")/_lib.sh"

require uv

cd api
exec uv run pytest "$@"
