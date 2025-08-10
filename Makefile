.PHONY: help install dev test clean lint format run-api run-web build

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install Python dependencies
	pip install -r api/requirements.txt

install-dev: ## Install development dependencies
	pip install -r api/requirements.txt
	pip install pytest pytest-asyncio black flake8

dev: ## Install development dependencies and setup pre-commit
	$(MAKE) install-dev

test: ## Run tests
	pytest api/tests/ -v

clean: ## Clean up Python cache files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/

lint: ## Run linting
	flake8 api/ --max-line-length=88 --extend-ignore=E203,W503
	black --check api/

format: ## Format code with black
	black api/ --line-length=88

run-api: ## Run the FastAPI server
	cd api && uvicorn main:app --reload --host 0.0.0.0 --port 8000

run-web: ## Run the Next.js frontend
	cd apps/web && npm run dev

build: ## Build the project
	python setup.py build

docker-up: ## Start Docker services
	docker-compose -f infra/docker-compose.yml up -d

docker-down: ## Stop Docker services
	docker-compose -f infra/docker-compose.yml down

docker-logs: ## View Docker logs
	docker-compose -f infra/docker-compose.yml logs -f
