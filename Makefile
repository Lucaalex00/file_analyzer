.DEFAULT_GOAL := help
.PHONY: help up down demo test test-e2e test-frontend-unit lint env

help: ## Show this help
	@grep -hE '^[a-z-]+:.*?## ' $(MAKEFILE_LIST) | awk -F':.*?## ' '{printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

env: ## Create a .env from .env.example (does nothing if .env already exists)
	@test -f .env || (cp .env.example .env && echo "Created .env — edit it with your Azure OpenAI credentials.")

up: ## Build and start the API (http://localhost:8000)
	docker compose up --build

demo: ## Start the API from the CI-published image — no local build
	docker compose -f docker-compose.yml -f docker-compose.prebuilt.yml up -d
	@echo "API http://localhost:8000"

down: ## Stop the stack
	docker compose down

test: ## Run the full test suite locally (needs a venv with requirements-dev.txt installed)
	pytest

test-e2e: ## Run Playwright e2e tests against the running stack (run `make up` first)
	cd e2e && npm ci && npx playwright install --with-deps chromium && npx playwright test

test-frontend-unit: ## Run frontend JS unit tests (no running stack needed)
	cd e2e && npm ci && npm run test:unit

lint: ## Run ruff
	ruff check src tests
