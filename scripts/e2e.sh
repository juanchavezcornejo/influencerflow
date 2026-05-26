#!/usr/bin/env bash
# Start the end-to-end test environment.
# Requires: docker-compose (for postgres + redis), python, node.
# Usage: ./scripts/e2e.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

log() { echo "  → $*"; }

# ── 1. Ensure docker services are running ──────────────────────────
log "Starting PostgreSQL + Redis via docker-compose..."
docker compose up -d postgres redis 2>/dev/null || true
sleep 2

# ── 2. Seed the test user ──────────────────────────────────────────
log "Seeding test user..."
cd "$ROOT/api"
SINGLE_USER_EMAIL="e2e@influencerflow.local" \
SINGLE_USER_PASSWORD="e2e-test-password" \
DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/influencerflow" \
  uv run python scripts/seed_user.py

# ── 3. Run migrations ──────────────────────────────────────────────
log "Running database migrations..."
DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/influencerflow" \
  uv run alembic upgrade head

# ── 4. Start the mocked e2e API ────────────────────────────────────
log "Starting mocked API on port 8001..."
cd "$ROOT/api"
DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/influencerflow" \
FERNET_KEY="test-fernet-key-do-not-use-in-production-1234567890==" \
JWT_SECRET="e2e-test-jwt-secret" \
CELERY_TASK_ALWAYS_EAGER="true" \
  uv run uvicorn app.testing.e2e_app:app --host 0.0.0.0 --port 8001 &
API_PID=$!
log "API PID: $API_PID"

# ── 5. Start Next.js dev server ────────────────────────────────────
log "Starting Next.js on port 3000..."
cd "$ROOT/web"
API_BASE="http://localhost:8001" pnpm dev --port 3000 &
WEB_PID=$!
log "Web PID: $WEB_PID"

# Wait for both servers
log "Waiting for servers to be ready..."
for i in $(seq 1 30); do
  if curl -s http://localhost:8001/api/v1/health > /dev/null 2>&1 && \
     curl -s http://localhost:3000 > /dev/null 2>&1; then
    log "Both servers ready!"
    break
  fi
  sleep 2
done

# ── 6. Run Playwright tests ────────────────────────────────────────
log "Running Playwright tests..."
cd "$ROOT/web"
mkdir -p e2e-screenshots
pnpm exec playwright test --reporter=list "$@"
TEST_EXIT=$?

# ── 7. Cleanup ─────────────────────────────────────────────────────
log "Stopping servers..."
kill $API_PID $WEB_PID 2>/dev/null || true

log "E2E tests completed with exit code: $TEST_EXIT"
exit $TEST_EXIT
