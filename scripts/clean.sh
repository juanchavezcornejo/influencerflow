#!/usr/bin/env bash
# Wipe build/install artifacts. Does NOT touch ./data (use clean-data.sh for that).
source "$(dirname "$0")/_lib.sh"

paths=(
  "api/.venv"
  "api/.pytest_cache"
  "api/.mypy_cache"
  "api/.ruff_cache"
  "api/.coverage"
  "api/htmlcov"
  "api/dist"
  "api/build"
  "web/node_modules"
  "web/.next"
  "web/.turbo"
  "web/playwright-report"
  "web/test-results"
)

for p in "${paths[@]}"; do
  if [[ -e "$p" ]]; then
    rm -rf "$p"
    ok "Removed $p"
  fi
done

# Python bytecode caches (recursive)
log "Removing __pycache__ directories"
find api -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true

ok "Clean complete"
