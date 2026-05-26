#!/usr/bin/env bash
# Typecheck + lint + unit tests for the web package.
source "$(dirname "$0")/_lib.sh"

require pnpm

cd web
step "pnpm typecheck" pnpm typecheck
step "pnpm lint"      pnpm lint
step "pnpm test"      pnpm test
