# Makefile for Lamish Projection Engine

.PHONY: help setup venv install db-up db-down db-init test demo clean

help: ## Show this help message
	@echo "Lamish Projection Engine - Make Commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

setup: venv install db-up db-init ## Complete setup (venv, deps, db)
	@echo "✅ Setup complete! Run 'source venv/bin/activate' to activate"

venv: ## Create virtual environment
	@if [ -d "venv" ]; then \
		echo "Virtual environment already exists. Remove it first with 'rm -rf venv' if you want to recreate it."; \
	else \
		/usr/bin/python3 -m venv venv --system-site-packages; \
		echo "✅ Virtual environment created"; \
	fi

install: ## Install dependencies (requires activated venv)
	. venv/bin/activate && python -m pip install --upgrade pip
	. venv/bin/activate && python -m pip install -r requirements.txt
	@echo "✅ Dependencies installed"

db-up: ## Start PostgreSQL and pgAdmin
	docker-compose up -d
	@echo "✅ Database services started"

db-down: ## Stop PostgreSQL and pgAdmin
	docker-compose down
	@echo "✅ Database services stopped"

db-init: ## Initialize database schema and seed data
	. venv/bin/activate && python scripts/init_db.py
	@echo "✅ Database initialized"

test: ## Run setup tests
	. venv/bin/activate && python test_setup.py

demo: ## Run the demo
	. venv/bin/activate && python demo.py

cli: ## Show CLI help
	. venv/bin/activate && python -m lamish_projection_engine.cli.main --help

clean: ## Clean up generated files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	@echo "✅ Cleaned up generated files"

format: ## Format code with black
	black lamish_projection_engine/
	@echo "✅ Code formatted"

lint: ## Run linting checks
	flake8 lamish_projection_engine/
	@echo "✅ Linting complete"