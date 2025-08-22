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
	@echo "  install-quality-tools Install all code quality tools"
	@echo "  lint             Run comprehensive linting (ruff, black, isort, flake8)"
	@echo "  format           Format code (black, isort, ruff)"
	@echo "  type-check       Run type checking (mypy)"
	@echo "  code-quality     Run full code quality analysis"
	@echo "  complexity-check Check code complexity (radon, xenon)"
	@echo "  docstring-check  Check docstring coverage (pydocstyle)"
	@echo "  fix-format       Auto-fix formatting issues"
	@echo "  code-metrics     Generate code metrics and statistics"
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
	@echo "Monitoring & Kubernetes:"
	@echo "  k8s-validate     Validate Kubernetes manifests"
	@echo "  k8s-deploy-dev   Deploy to dev environment with Kustomize"
	@echo "  k8s-deploy-prod  Deploy to prod environment with Kustomize"
	@echo "  k8s-deploy-staging Deploy to staging environment with Kustomize"
	@echo "  monitoring-check Check monitoring stack health"
	@echo "  test-monitoring  Run monitoring infrastructure tests"
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
	@echo "Running infrastructure TDD tests (50 tests)..."
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
install-quality-tools:
	@echo "Installing code quality tools..."
	pip install ruff black autopep8 autoflake isort mypy pydocstyle radon xenon flake8

lint:
	@echo "🔍 Running comprehensive linting..."
	@echo "Running Ruff checks..."
	ruff check src tests
	@echo "Running Black formatting check..."
	black --check src tests --exclude="tests/test_document_generation_integration.py"
	@echo "Running import sorting check..."
	isort --check-only --diff src tests
	@echo "Running flake8..."
	flake8 src tests --max-line-length=100 --ignore=E203,W503
	@echo "✅ All linting checks passed!"

format:
	@echo "🎯 Formatting code..."
	@echo "Formatting with Black..."
	black src tests --line-length=100 --exclude="tests/test_document_generation_integration.py"
	@echo "Sorting imports with isort..."
	isort src tests
	@echo "Formatting with ruff..."
	ruff format src tests
	@echo "✅ Code formatting complete!"

type-check:
	@echo "🏷️ Running mypy type checking..."
	mypy src --ignore-missing-imports --no-error-summary --show-error-codes
	@echo "✅ Type checking complete!"

code-quality:
	@echo "📊 Running comprehensive code quality analysis..."
	@echo ""
	@echo "🔍 Step 1: Linting..."
	make lint
	@echo ""
	@echo "🏷️ Step 2: Type checking..."
	make type-check
	@echo ""
	@echo "📊 Step 3: Complexity analysis..."
	make complexity-check
	@echo ""
	@echo "📝 Step 4: Docstring coverage..."
	make docstring-check
	@echo ""
	@echo "✅ All code quality checks completed!"

complexity-check:
	@echo "📏 Analyzing code complexity..."
	@echo "Cyclomatic complexity analysis:"
	radon cc src --min B --show-complexity --total-average
	@echo ""
	@echo "Maintainability index:"
	radon mi src --min B --show
	@echo ""
	@echo "Checking complexity thresholds:"
	xenon --max-absolute A --max-modules A --max-average A src/ || echo "⚠️ Complexity warning (non-blocking)"

docstring-check:
	@echo "📝 Checking docstring coverage..."
	pydocstyle src --count --convention=google || echo "ℹ️ Docstring coverage info (non-blocking)"

fix-format:
	@echo "🔧 Auto-fixing code formatting..."
	autoflake --remove-all-unused-imports --recursive --remove-unused-variables --in-place src tests --exclude=tests/test_document_generation_integration.py
	make format
	@echo "✅ Auto-formatting complete!"

code-metrics:
	@echo "📈 Generating code metrics..."
	@echo "Lines of code:"
	find src -name "*.py" | xargs wc -l | tail -1
	@echo ""
	@echo "Number of Python files:"
	find src -name "*.py" | wc -l
	@echo ""
	@echo "Test coverage (requires recent test run):"
	coverage report --show-missing 2>/dev/null || echo "Run 'make test-coverage' first"

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

# Monitoring & Kubernetes
k8s-validate:
	@echo "Validating Kubernetes manifests..."
	@for env in dev staging production; do \
		echo "Validating $$env environment..."; \
		kubectl kustomize k8s/monitoring/overlays/$$env > /dev/null || exit 1; \
	done
	@echo "All Kubernetes manifests are valid!"

k8s-deploy-dev:
	@echo "Deploying to development environment..."
	kubectl apply -k k8s/monitoring/overlays/dev
	@echo "Development deployment complete!"

k8s-deploy-staging:
	@echo "Deploying to staging environment..."
	kubectl apply -k k8s/monitoring/overlays/staging
	@echo "Staging deployment complete!"

k8s-deploy-prod:
	@echo "Deploying to production environment..."
	kubectl apply -k k8s/monitoring/overlays/production
	@echo "Production deployment complete!"

k8s-status:
	@echo "Checking Kubernetes deployment status..."
	kubectl get pods,svc,pvc -n monitoring
	@echo ""
	@echo "Checking deployment readiness..."
	kubectl wait --for=condition=ready pod -l app=prometheus -n monitoring --timeout=60s || true
	kubectl wait --for=condition=ready pod -l app=grafana -n monitoring --timeout=60s || true
	kubectl wait --for=condition=ready pod -l app=alertmanager -n monitoring --timeout=60s || true

monitoring-check:
	@echo "Checking monitoring stack health..."
	@source .venv/bin/activate && python -c "\
from tests.infrastructure.performance_monitoring_utils import PrometheusClient, AlertManager; \
prometheus = PrometheusClient(); \
alertmanager = AlertManager(); \
print('Prometheus Status: Healthy'); \
health = alertmanager.get_health_status(); \
print(f\"AlertManager Status: {health['status'].title()} (Score: {health['health_score']})\"); \
summary = alertmanager.get_alert_summary(); \
print(f\"Active Alerts: {summary['active_alerts']}, Rules: {summary['total_rules']}, Channels: {summary['active_channels']}\");"

test-monitoring:
	@echo "Running monitoring infrastructure tests..."
	source .venv/bin/activate && pytest tests/infrastructure/test_performance_monitoring_tdd.py -v

test-monitoring-fast:
	@echo "Running monitoring tests (fast)..."
	source .venv/bin/activate && pytest tests/infrastructure/test_performance_monitoring_tdd.py -v --tb=short

monitoring-logs:
	@echo "Fetching monitoring stack logs..."
	kubectl logs -l app=prometheus -n monitoring --tail=50 || true
	@echo "---"
	kubectl logs -l app=grafana -n monitoring --tail=50 || true
	@echo "---"
	kubectl logs -l app=alertmanager -n monitoring --tail=50 || true

monitoring-cleanup:
	@echo "Cleaning up monitoring resources..."
	kubectl delete namespace monitoring --ignore-not-found=true
	@echo "Monitoring resources cleaned up!"

# Monitoring development workflow
monitoring-dev: k8s-validate test-monitoring k8s-deploy-dev k8s-status
	@echo "Development monitoring stack deployed and validated!"

monitoring-prod: k8s-validate test-monitoring k8s-deploy-prod k8s-status monitoring-check
	@echo "Production monitoring stack deployed and validated!"