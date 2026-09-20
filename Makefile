.DEFAULT_GOAL := help
.PHONY: help up down demo test test-local test-e2e test-frontend-unit eval eval-update lint env

help: ## Show this help
	@grep -hE '^[a-z-]+:.*?## ' $(MAKEFILE_LIST) | awk -F':.*?## ' '{printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

env: ## Create a .env from .env.example (does nothing if .env already exists)
	@test -f .env || (cp .env.example .env && echo "Created .env — edit it with your Azure OpenAI credentials.")

up: ## Build and start the API (http://localhost:8000)
	docker compose up --build

demo: ## Start the API from the CI-published image, no local build, no credentials needed (demo mode)
	docker compose -f docker-compose.yml -f docker-compose.prebuilt.yml up -d
	@echo "API http://localhost:8000 (demo mode unless AZURE_OPENAI_* is set in .env)"

down: ## Stop the stack
	docker compose down

test: ## Run the backend test suite in the running container (no local Python needed)
	docker compose exec api python -m pytest

test-local: ## Run the backend test suite on the host (needs a venv with requirements-dev.txt installed)
	pytest

eval: ## Run the quality eval against the real model (needs credentials, costs calls)
	docker compose exec api python -m pytest tests/eval/test_live_quality.py -m live -v

eval-update: ## Re-record the eval baseline from the current run (read the diff before committing)
	docker compose exec -e UPDATE_EVAL_BASELINE=1 api python -m pytest tests/eval/test_live_quality.py -m live -v

test-e2e: ## Run Playwright e2e tests against the running stack (run `make up` first)
	cd e2e && npm ci && npx playwright install --with-deps chromium && npx playwright test

test-frontend-unit: ## Run frontend JS unit tests (no running stack needed)
	cd e2e && npm ci && npm run test:unit

lint: ## Run ruff
	ruff check src tests
