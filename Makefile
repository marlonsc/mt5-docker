# =============================================================================
# MetaTrader5 Docker - Makefile
# =============================================================================
# Comprehensive build, test, and deployment automation
#
# Usage:
#   make help              # Show this help
#   make install           # Install all dependencies
#   make test              # Run all tests
#   make build             # Build Docker image
#   make run               # Run container with docker-compose
#   make clean             # Clean up build artifacts
# =============================================================================

# =============================================================================
# Configuration
# =============================================================================

# Python and tools
PYTHON := python3.13
POETRY := poetry
PIP := pip3

# Docker
DOCKER := docker
DOCKER_COMPOSE := docker compose
IMAGE_NAME := marlonsc/mt5-docker
IMAGE_TAG := debian

# Project paths
PROJECT_ROOT := .
DOCKER_DIR := docker
SCRIPTS_DIR := scripts
TESTS_DIR := tests

# Required environment variables for production builds
REQUIRED_ENV_VARS := MT5_LOGIN MT5_PASSWORD VNC_PASSWORD

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

# =============================================================================
# Development Environment
# =============================================================================

.PHONY: install
install: ## Install all dependencies (Poetry + system)
	@echo "$(BLUE)Installing dependencies...$(NC)"
	@$(PIP) install --upgrade pip poetry
	@$(POETRY) install
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

.PHONY: install-dev
install-dev: ## Install development dependencies only
	@echo "$(BLUE)Installing development dependencies...$(NC)"
	@$(PIP) install --upgrade pip poetry
	@$(POETRY) install --with dev
	@echo "$(GREEN)✓ Development dependencies installed$(NC)"

.PHONY: setup
setup: ## Setup development environment (dependencies + config)
	@echo "$(BLUE)Setting up development environment...$(NC)"
	@$(MAKE) install
	@$(MAKE) setup-deps
	@if [ ! -f .env ]; then \
		cp config.env.template .env && \
		echo "$(YELLOW)⚠️  Created .env file from template$(NC)"; \
		echo "$(YELLOW)💡 IMPORTANT: Edit .env and set your credentials before building:$(NC)"; \
		echo "   - MT5_LOGIN (your account number)"; \
		echo "   - MT5_PASSWORD (your account password)"; \
		echo "   - VNC_PASSWORD (web interface password)"; \
	fi
	@echo "$(GREEN)✓ Development environment ready$(NC)"
	@echo "$(YELLOW)🔍 Run 'make show-env-status' to check your .env configuration$(NC)"

.PHONY: setup-deps
setup-deps: ## Configure mt5linux dependency (auto-detects environment)
	@echo "$(BLUE)Configuring dependencies...$(NC)"
	@./$(SCRIPTS_DIR)/setup-dependencies.sh
	@echo "$(GREEN)✓ Dependencies configured$(NC)"

# =============================================================================
# Testing
# =============================================================================

.PHONY: test
test: ## Run all tests (static + runtime if container available)
	@echo "$(BLUE)Running all tests...$(NC)"
	@$(POETRY) run pytest $(TESTS_DIR)/ -v --tb=short
	@echo "$(GREEN)✓ All tests passed$(NC)"

.PHONY: test-static
test-static: ## Run static tests only (no container needed)
	@echo "$(BLUE)Running static tests...$(NC)"
	@$(POETRY) run pytest $(TESTS_DIR)/test_static.py -v
	@echo "$(GREEN)✓ Static tests passed$(NC)"

.PHONY: test-cov
test-cov: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	@$(POETRY) run pytest $(TESTS_DIR)/ --cov=. --cov-report=html --cov-report=term
	@echo "$(GREEN)✓ Coverage report generated$(NC)"

.PHONY: test-quick
test-quick: ## Run tests quickly (stop on first failure)
	@echo "$(BLUE)Running quick tests...$(NC)"
	@$(POETRY) run pytest $(TESTS_DIR)/ -x --tb=short
	@echo "$(GREEN)✓ Quick tests passed$(NC)"

# =============================================================================
# Code Quality
# =============================================================================

.PHONY: lint
lint: ## Run all linting tools
	@echo "$(BLUE)Running linters...$(NC)"
	@$(POETRY) run ruff check .
	@$(POETRY) run mypy . --ignore-missing-imports
	@echo "$(GREEN)✓ Linting passed$(NC)"

.PHONY: format
format: ## Format code with ruff
	@echo "$(BLUE)Formatting code...$(NC)"
	@$(POETRY) run ruff format .
	@$(POETRY) run ruff check . --fix
	@echo "$(GREEN)✓ Code formatted$(NC)"

.PHONY: type-check
type-check: ## Run type checking only
	@echo "$(BLUE)Running type checks...$(NC)"
	@$(POETRY) run mypy . --ignore-missing-imports
	@echo "$(GREEN)✓ Type checking passed$(NC)"

.PHONY: check
check: ## Run all code quality checks (lint + format + test)
	@echo "$(BLUE)Running all checks...$(NC)"
	@$(MAKE) lint
	@$(MAKE) format
	@$(MAKE) test
	@echo "$(GREEN)✓ All checks passed$(NC)"

# =============================================================================
# Docker Operations
# =============================================================================

.PHONY: build
build: validate-env ## Build Docker image (requires valid .env)
	@echo "$(BLUE)Building Docker image...$(NC)"
	@cd $(DOCKER_DIR) && $(DOCKER_COMPOSE) build
	@echo "$(GREEN)✓ Docker image built$(NC)"

.PHONY: build-no-cache
build-no-cache: ## Build Docker image without cache
	@echo "$(BLUE)Building Docker image (no cache)...$(NC)"
	@cd $(DOCKER_DIR) && $(DOCKER_COMPOSE) build --no-cache
	@echo "$(GREEN)✓ Docker image built (no cache)$(NC)"

.PHONY: run
run: validate-env ## Run container with docker-compose (requires valid .env)
	@echo "$(BLUE)Starting container...$(NC)"
	@cd $(DOCKER_DIR) && $(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)✓ Container started$(NC)"
	@echo "$(YELLOW)🌐 Access MT5 at: http://localhost:3000$(NC)"
	@echo "$(YELLOW)🔑 VNC Password: $(shell grep '^VNC_PASSWORD=' .env | cut -d'=' -f2)$(NC)"

.PHONY: run-logs
run-logs: ## Run container and show logs
	@echo "$(BLUE)Starting container with logs...$(NC)"
	@cd $(DOCKER_DIR) && $(DOCKER_COMPOSE) up

.PHONY: stop
stop: ## Stop running containers
	@echo "$(BLUE)Stopping containers...$(NC)"
	@cd $(DOCKER_DIR) && $(DOCKER_COMPOSE) down
	@echo "$(GREEN)✓ Containers stopped$(NC)"

.PHONY: restart
restart: ## Restart containers
	@echo "$(BLUE)Restarting containers...$(NC)"
	@$(MAKE) stop
	@$(MAKE) run

.PHONY: logs
logs: ## Show container logs
	@echo "$(BLUE)Showing container logs...$(NC)"
	@cd $(DOCKER_DIR) && $(DOCKER_COMPOSE) logs -f

.PHONY: shell
shell: ## Open shell in running container
	@echo "$(BLUE)Opening shell in container...$(NC)"
	@cd $(DOCKER_DIR) && $(DOCKER_COMPOSE) exec mt5 bash

# =============================================================================
# Docker Image Management
# =============================================================================

.PHONY: push
push: ## Push Docker image to registry
	@echo "$(BLUE)Pushing Docker image...$(NC)"
	@$(DOCKER) push $(IMAGE_NAME):$(IMAGE_TAG)
	@echo "$(GREEN)✓ Image pushed$(NC)"

.PHONY: pull
pull: ## Pull latest Docker image
	@echo "$(BLUE)Pulling Docker image...$(NC)"
	@$(DOCKER) pull $(IMAGE_NAME):$(IMAGE_TAG)
	@echo "$(GREEN)✓ Image pulled$(NC)"

.PHONY: clean-images
clean-images: ## Remove unused Docker images
	@echo "$(BLUE)Cleaning Docker images...$(NC)"
	@$(DOCKER) image prune -f
	@echo "$(GREEN)✓ Images cleaned$(NC)"

# =============================================================================
# Dependency Management
# =============================================================================

.PHONY: update-deps
update-deps: ## Update all dependencies
	@echo "$(BLUE)Updating dependencies...$(NC)"
	@$(POETRY) update
	@echo "$(GREEN)✓ Dependencies updated$(NC)"

.PHONY: lock
lock: ## Update poetry.lock file
	@echo "$(BLUE)Updating lock file...$(NC)"
	@$(POETRY) lock
	@echo "$(GREEN)✓ Lock file updated$(NC)"

.PHONY: export-requirements
export-requirements: ## Export requirements.txt for CI/CD
	@echo "$(BLUE)Exporting requirements...$(NC)"
	@$(POETRY) export -f requirements.txt --output requirements.txt
	@echo "$(GREEN)✓ Requirements exported$(NC)"

# =============================================================================
# Cleanup
# =============================================================================

.PHONY: clean
clean: ## Clean up build artifacts and caches
	@echo "$(BLUE)Cleaning up...$(NC)"
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type f -name ".coverage" -delete 2>/dev/null || true
	@rm -rf .pytest_cache htmlcov .mypy_cache .ruff_cache
	@echo "$(GREEN)✓ Cleanup completed$(NC)"

.PHONY: clean-all
clean-all: clean ## Clean everything including dependencies
	@echo "$(BLUE)Cleaning everything...$(NC)"
	@rm -rf .venv poetry.lock
	@$(MAKE) clean-images
	@echo "$(GREEN)✓ Full cleanup completed$(NC)"

.PHONY: clean-docker
clean-docker: ## Stop and remove all Docker containers and volumes
	@echo "$(BLUE)Cleaning Docker...$(NC)"
	@cd $(DOCKER_DIR) && $(DOCKER_COMPOSE) down -v --remove-orphans
	@$(DOCKER) system prune -f
	@echo "$(GREEN)✓ Docker cleaned$(NC)"

# =============================================================================
# CI/CD
# =============================================================================

.PHONY: ci
ci: ## Run CI pipeline locally (includes env validation)
	@echo "$(BLUE)Running CI pipeline...$(NC)"
	@$(MAKE) install-dev
	@$(MAKE) check
	@$(MAKE) validate-env
	@$(MAKE) build
	@echo "$(GREEN)✓ CI pipeline passed$(NC)"

.PHONY: ci-test
ci-test: ## Run CI tests only
	@echo "$(BLUE)Running CI tests...$(NC)"
	@$(MAKE) test
	@$(MAKE) lint
	@echo "$(GREEN)✓ CI tests passed$(NC)"

# =============================================================================
# Documentation
# =============================================================================

.PHONY: docs
docs: ## Generate documentation
	@echo "$(BLUE)Generating documentation...$(NC)"
	@echo "Documentation generation not implemented yet"
	@echo "$(YELLOW)⚠️  TODO: Add documentation generation$(NC)"

# =============================================================================
# Utility
# =============================================================================

.PHONY: version
version: ## Show version information
	@echo "$(BLUE)Version Information:$(NC)"
	@echo "Python: $$(python3 --version)"
	@echo "Poetry: $$(poetry --version 2>/dev/null || echo 'Not installed')"
	@echo "Docker: $$(docker --version)"
	@echo "Project: $$(grep '^    version = ' pyproject.toml | sed 's/.*= *"\([^"]*\)".*/\1/')"

.PHONY: health
health: ## Check system health
	@echo "$(BLUE)System Health Check:$(NC)"
	@echo "✓ Python: $$(python3 --version)"
	@echo "✓ Poetry: $$(poetry --version 2>/dev/null || echo '✗ Not installed')"
	@echo "✓ Docker: $$(docker --version)"
	@echo "✓ Git: $$(git --version)"
	@echo "✓ Tests: $$(poetry run pytest --collect-only -q 2>/dev/null | wc -l) tests found"

.PHONY: help
help: ## Show this help message
	@echo "$(BLUE)MetaTrader5 Docker - Available Commands:$(NC)"
	@echo ""
	@echo "Development:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E "(install|setup|test|lint|format|check)" | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "Docker:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E "(build|run|stop|logs|shell)" | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "Maintenance:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E "(clean|update|version|health)" | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "For more details, see README.md"

# =============================================================================
# Environment Validation
# =============================================================================

.PHONY: validate-env
validate-env: ## Validate that required environment variables are set
	@echo "$(BLUE)Validating environment variables...$(NC)"
	@if [ ! -f .env ]; then \
		echo "$(RED)❌ Error: .env file not found$(NC)"; \
		echo "$(YELLOW)💡 Copy config.env.template to .env and fill in your values:$(NC)"; \
		echo "   cp config.env.template .env"; \
		exit 1; \
	fi
	@for var in $(REQUIRED_ENV_VARS); do \
		if ! grep -q "^$${var}=" .env || grep -q "^$${var}=\s*$$" .env; then \
			echo "$(RED)❌ Error: $${var} is not set in .env file$(NC)"; \
			echo "$(YELLOW)💡 Please set $${var} in your .env file$(NC)"; \
			exit 1; \
		fi; \
	done
	@echo "$(GREEN)✓ All required environment variables are set$(NC)"

.PHONY: show-env-status
show-env-status: ## Show status of required environment variables
	@echo "$(BLUE)Environment Variables Status:$(NC)"
	@if [ ! -f .env ]; then \
		echo "$(RED)❌ .env file not found$(NC)"; \
		exit 1; \
	fi
	@for var in $(REQUIRED_ENV_VARS); do \
		if grep -q "^$${var}=" .env && ! grep -q "^$${var}=\s*$$" .env; then \
			echo "$(GREEN)✓ $${var} is set$(NC)"; \
		else \
			echo "$(RED)❌ $${var} is not set$(NC)"; \
		fi; \
	done

# =============================================================================
# Default Target
# =============================================================================

.DEFAULT_GOAL := help
