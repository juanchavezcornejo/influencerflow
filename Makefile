# InfluencerFlow — thin wrappers over scripts/*.sh
#
# Every target delegates to the matching script so behavior stays in one place.
# Run `make help` for the catalog.

.DEFAULT_GOAL := help
.PHONY: help bootstrap setup-credentials dev dev-api dev-web test test-api test-web \
        lint format build clean clean-data migrate migrate-new reset-db \
        logs shell-api ps

help:  ## Show this help
	@awk 'BEGIN { FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n\nTargets:\n" } \
	/^[a-zA-Z_-]+:.*##/ { printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

bootstrap:        ## First-time setup (uv sync + pnpm install + .env files)
	@./scripts/bootstrap.sh

setup-credentials: ## Re-run credential setup (update .env files)
	@./scripts/setup-credentials.sh

dev:              ## Start full stack (docker compose up)
	@./scripts/dev.sh

dev-api:     ## Start api + worker + infra only
	@./scripts/dev-api.sh

dev-web:     ## Start Next.js dev server standalone
	@./scripts/dev-web.sh

test:        ## Run all tests (api + web)
	@./scripts/test.sh

test-api:    ## Pytest only
	@./scripts/test-api.sh

test-web:    ## Web typecheck + lint + tests
	@./scripts/test-web.sh

lint:        ## Non-mutating checks (ruff + mypy + eslint + prettier --check)
	@./scripts/lint.sh

format:      ## Auto-format + auto-fix
	@./scripts/format.sh

build:       ## Production build (next build + docker build)
	@./scripts/build.sh

clean:       ## Remove build/install caches (keeps ./data)
	@./scripts/clean.sh

clean-data:  ## Wipe ./data volume (prompts first)
	@./scripts/clean-data.sh

migrate:     ## alembic upgrade head
	@./scripts/migrate.sh

migrate-new: ## alembic revision --autogenerate -m "msg"  (make migrate-new msg="add users")
	@./scripts/migrate-new.sh "$(msg)"

reset-db:    ## Drop + recreate dev DB, then migrate (prompts first)
	@./scripts/reset-db.sh

logs:        ## Tail docker compose logs (make logs svc=api for one service)
	@./scripts/logs.sh $(svc)

shell-api:   ## Python REPL inside the api container
	@./scripts/shell-api.sh

ps:          ## docker compose ps + health probes
	@./scripts/ps.sh
