#!/usr/bin/env bash
# Run all tests (api + web).
source "$(dirname "$0")/_lib.sh"

step "API tests"     "$REPO_ROOT/scripts/test-api.sh"
step "Web checks"    "$REPO_ROOT/scripts/test-web.sh"

ok "All tests passed"
