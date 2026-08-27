.DEFAULT_GOAL := help
.PHONY: help up down demo test lint env

help: ## Show this help
	@grep -hE '^[a-z-]+:.*?## ' $(MAKEFILE_LIST) | awk -F':.*?## ' '{printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

env: ## Create a .env from .env.example (does nothing if .env already exists)
	@test -f .env || (cp .env.example .env && echo "Created .env — edit it with your Azure OpenAI credentials.")

up: ## Build and start the API (http://localhost:8000)
	docker compose up --build

down: ## Stop the stack
	docker compose down

test: ## Run the full test suite locally (needs a venv with requirements-dev.txt installed)
	pytest

lint: ## Run ruff
	ruff check src tests
