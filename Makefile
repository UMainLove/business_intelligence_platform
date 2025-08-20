# Makefile for Business Intelligence Platform

.PHONY: help install test test-unit test-integration test-functionality test-advanced test-infrastructure test-coverage lint format clean docker-build docker-run

# Default target
help:
	@echo "Business Intelligence Platform - Available Commands:"
	@echo ""
	@echo "Setup:"
	@echo "  install          Install dependencies"
	@echo "  install-dev      Install development dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  test             Run all tests"
	@echo "  test-synthetic   Run synthetic tests only (no external deps)"
	@echo "  test-unit        Run unit tests only"
	@echo "  test-integration Run integration tests only"
	@echo "  test-functionality Run functionality tests only"
	@echo "  test-advanced    Run advanced tests only"
	@echo "  test-infrastructure Run infrastructure tests only"
	@echo "  test-coverage    Run tests with coverage report"
	@echo "  test-fast        Run tests excluding slow ones"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint             Run linting checks"
	@echo "  format           Format code"
	@echo "  type-check       Run type checking"
	@echo ""
	@echo "Application:"
	@echo "  run              Run the application"
	@echo "  run-dev          Run in development mode"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build     Build Docker image"
	@echo "  docker-run       Run Docker container"
	@echo "  docker-compose   Run with docker-compose"
	@echo ""
	@echo "Database:"
	@echo "  db-init          Initialize database"
	@echo "  db-migrate       Run database migrations"
	@echo ""
	@echo "Utilities:"
	@echo "  clean            Clean temporary files"
	@echo "  health-check     Check system health"

# Installation
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install black flake8 mypy isort

# Testing
test:
	source .venv/bin/activate && python scripts/run_tests.py

test-synthetic:
	@echo "Running synthetic tests (no external dependencies)..."
	pytest tests/test_*_synthetic.py -v --tb=short

test-unit:
	source .venv/bin/activate && python scripts/run_tests.py --unit

test-integration:
	source .venv/bin/activate && python scripts/run_tests.py --integration

test-functionality:
	@echo "Running functionality tests (77 tests)..."
	source .venv/bin/activate && pytest tests/test_*_functionality.py -v --tb=short

test-advanced:
	@echo "Running advanced tests (39 tests)..."
	source .venv/bin/activate && pytest tests/test_similarity_search_advanced.py tests/test_redis_caching_comprehensive.py -v --tb=short

test-infrastructure:
	@echo "Running infrastructure TDD tests (9 tests)..."
	source .venv/bin/activate && pytest tests/infrastructure/ -v --tb=short

test-coverage:
	source .venv/bin/activate && python scripts/run_tests.py --coverage

test-fast:
	source .venv/bin/activate && python scripts/run_tests.py

test-verbose:
	source .venv/bin/activate && python scripts/run_tests.py --verbose

test-parallel:
	source .venv/bin/activate && python scripts/run_tests.py --parallel

# Code Quality
lint:
	@echo "Running flake8..."
	flake8 src tests --max-line-length=100 --ignore=E203,W503
	@echo "Running imports check..."
	isort --check-only src tests

format:
	@echo "Formatting with black..."
	black src tests --line-length=100
	@echo "Sorting imports..."
	isort src tests

type-check:
	@echo "Running mypy type checking..."
	mypy src --ignore-missing-imports

# Application
run:
	streamlit run app_bi.py

run-dev:
	ENVIRONMENT=development streamlit run app_bi.py

# Docker
docker-build:
	docker build -t business-intelligence:latest .

docker-run:
	docker run -p 8501:8501 business-intelligence:latest

docker-compose:
	docker-compose up -d

docker-compose-dev:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Database
db-init:
	source .venv/bin/activate && python -c "from src.database_config import db_config; db_config.init_database(); print('Database initialized')"

db-migrate:
	@echo "Running database migrations..."
	# Add migration commands here when implemented

# Health and Monitoring
health-check:
	source .venv/bin/activate && python -c "from src.health_monitor import health_monitor; import json; print(json.dumps(health_monitor.get_comprehensive_health(), indent=2))"

# Utilities
clean:
	@echo "Cleaning temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .coverage htmlcov/ .pytest_cache/
	rm -rf dist/ build/

clean-all: clean
	rm -rf data/generated_docs/ data/sessions/ data/*.db

# Development setup
setup-dev: install-dev
	@echo "Setting up development environment..."
	pre-commit install || echo "pre-commit not available"
	mkdir -p data/generated_docs data/sessions logs
	@echo "Development environment ready!"

# CI/CD helpers
ci-test:
	source .venv/bin/activate && python scripts/run_tests.py --coverage --parallel

ci-lint:
	flake8 src tests --max-line-length=100 --ignore=E203,W503
	isort --check-only src tests
	black --check src tests --line-length=100

ci-type-check:
	mypy src --ignore-missing-imports

# Security scanning
security-scan:
	@echo "Running security scan..."
	pip-audit || echo "pip-audit not available, install with: pip install pip-audit"

# Documentation
docs-build:
	@echo "Building documentation..."
	# Add documentation build commands here

# Performance testing
perf-test:
	@echo "Running performance tests..."
	source .venv/bin/activate && python -c "from tests.test_integration import TestSystemPerformance; t = TestSystemPerformance(); t.test_multiple_financial_calculations(); print('Performance tests passed')"

# Full CI pipeline
ci: ci-lint ci-type-check ci-test
	@echo "All CI checks passed!"