# Unified Tech Intelligence Platform - Development Commands

.PHONY: help install test test-fast test-all test-lido test-github test-basic test-cov clean lint format check extract-github extract-lido extract-lido-full data-status merge-databases setup-unified

# Default target
help:
	@echo "🚀 Unified Tech Intelligence Platform - Available Commands"
	@echo "=========================================================="
	@echo "Setup:"
	@echo "  install        - Install dependencies including test dependencies"
	@echo "  setup-unified  - Set up unified tech_intel.duckdb with sample data"
	@echo ""
	@echo "Data Extraction:"
	@echo "  extract-sample     - Extract sample GitHub + Catalyst data to tech_intel.duckdb"
	@echo "  extract-lido-full  - Run full Lido Catalyst ecosystem extraction"
	@echo "  data-status        - Show current database status and record counts"
	@echo ""
	@echo "dbt Analytics:"
	@echo "  dbt-run-github    - Run GitHub dbt models only"
	@echo "  dbt-run-catalyst  - Run Catalyst dbt models only"  
	@echo "  dbt-run-all       - Run all dbt models (GitHub + Catalyst)"
	@echo "  dbt-test          - Run dbt tests on models"
	@echo "  dbt-docs-github   - Generate GitHub dbt documentation"
	@echo "  dbt-docs-catalyst - Generate Catalyst dbt documentation"
	@echo "  dbt-clean         - Clean dbt artifacts"
	@echo "  analytics-full    - Full pipeline: extract-sample + dbt-run-all"
	@echo ""
	@echo "Testing:"
	@echo "  test           - Run fast unit tests (GitHub + Lido, ~0.7s)"
	@echo "  test-all       - Run all tests including slow API tests"
	@echo "  test-lido      - Run only Lido connector unit tests (fast)"
	@echo "  test-github    - Run only GitHub connector unit tests (fast)"
	@echo "  test-integration - Run API integration tests (makes real API calls)"
	@echo "  test-basic     - Run basic infrastructure tests"
	@echo "  test-cov       - Run tests with coverage report"
	@echo ""
	@echo "Quality:"
	@echo "  lint        - Run linting checks"
	@echo "  format      - Format code with black and ruff"
	@echo "  check       - Run all quality checks (lint + tests)"
	@echo ""
	@echo "Cleanup:"
	@echo "  clean       - Remove test artifacts and temp files"

# Installation
install:
	uv sync --extra test

install-dev:
	uv sync --extra test --dev

# Testing
test:
	@echo "🚀 Running fast tests (excluding slow API tests)..."
	uv run python -m pytest tests/ -v -m "not slow and not integration"

test-all:
	@echo "🚀 Running all tests (including slow API tests)..."
	uv run python -m pytest tests/ -v

test-lido:
	@echo "🚀 Running Lido connector tests..."
	uv run python -m pytest tests/connectors/test_lido.py -v -m "not slow and not integration"

test-github:
	@echo "🚀 Running GitHub connector tests..."
	uv run python -m pytest tests/connectors/test_github.py -v -m "not slow and not integration"

test-integration:
	@echo "🚀 Running integration tests (makes API calls)..."
	uv run python -m pytest tests/ -v -m "integration"

test-basic:
	@echo "🚀 Running basic infrastructure tests..."
	uv run python -m pytest tests/test_basic.py -v

test-cov:
	@echo "🚀 Running tests with coverage report..."
	uv run python -m pytest tests/ --cov=src --cov-report=html --cov-report=term-missing

# Unified Data Extraction - Single Database
extract-sample:
	@echo "🚀 Running sample data extraction (GitHub + Catalyst)..."
	uv run python scripts/extract_all.py
	@echo "✅ Sample extraction completed - check tech_intel.duckdb"

extract-lido-full:
	@echo "🚀 Running FULL Lido Catalyst ecosystem extraction..."
	@echo "⚠️  This will take several minutes and download ~10k proposals"
	@read -p "Continue? [y/N] " confirm && [ "$$confirm" = "y" ] || exit 1
	uv run python -c "import dlt; from src.cardano_insights.connectors.lido import funds, proposals; pipeline = dlt.pipeline(pipeline_name='tech_intel', destination='duckdb', dataset_name='lido_raw'); print('Loading all funds...'); pipeline.run(funds(), table_name='funds'); print('Loading ALL proposals (this will take time)...'); pipeline.run(proposals(), table_name='proposals')"
	@echo "✅ Lido full extraction completed"

setup-unified: extract-sample
	@echo "🎯 Unified tech intelligence platform setup completed!"
	@echo "📊 Single database at tech_intel.duckdb ready for analytics"

data-status:
	@echo "📊 Unified Tech Intelligence Database Status"
	@echo "============================================"
	@if [ -f "tech_intel.duckdb" ]; then \
		echo "🎯 tech_intel.duckdb (single unified database):"; \
		uv run python scripts/check_status.py; \
	else \
		echo "❌ tech_intel.duckdb not found - run 'make setup-unified' to create"; \
	fi

# Code Quality (optional - can be added later)
lint:
	@echo "🔍 Running linting checks..."
	@echo "Note: Install ruff/black for full linting support"
	uv run python -m py_compile src/cardano_insights/connectors/lido.py

format:
	@echo "🎨 Code formatting not configured yet"
	@echo "Consider adding ruff/black to project dependencies"

check: lint test
	@echo "✅ All quality checks completed"

# Cleanup
clean:
	@echo "🧹 Cleaning up test artifacts and temporary files..."
	find . -name "*test*.duckdb" -type f -delete 2>/dev/null || true
	find . -name "*.duckdb.wal" -type f -delete 2>/dev/null || true
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name "htmlcov" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name ".coverage" -delete 2>/dev/null || true
	@echo "✅ Cleanup completed (essential databases preserved)"

clean-all: clean
	@echo "🚨 WARNING: This will delete ALL databases including source data!"
	@read -p "Continue? [y/N] " confirm && [ "$$confirm" = "y" ] || exit 1
	find . -name "*.duckdb" -type f -delete
	@echo "💥 All databases deleted - you'll need to run 'make setup-unified' to recreate"

# Development workflow
dev-setup: install
	@echo "🛠️  Development environment ready!"
	@echo "Run 'make test' to verify everything works"

# dbt Analytics Commands
dbt-run-github:
	@echo "🔄 Running GitHub dbt models (bronze → silver → gold)..."
	uv run dbt run --project-dir analytics/dbt_github --profiles-dir . --profile tech_intel

dbt-run-catalyst:
	@echo "🔄 Running Catalyst dbt models (bronze → silver → gold)..."
	cd analytics/dbt_catalyst && uv run dbt run --profiles-dir ../../ --profile tech_intel

dbt-run-all: dbt-run-github dbt-run-catalyst
	@echo "✅ All dbt models completed (GitHub + Catalyst)!"

dbt-test:
	@echo "🧪 Running dbt tests..."
	uv run dbt test --project-dir analytics/dbt_github --profiles-dir . --profile tech_intel
	uv run dbt test --project-dir analytics/dbt_catalyst --profiles-dir . --profile tech_intel

dbt-docs-github:
	@echo "📖 Generating GitHub dbt documentation..."
	cd analytics/dbt_github && uv run dbt docs generate --profiles-dir ../../ --profile tech_intel
	cd analytics/dbt_github && uv run dbt docs serve --port 8080 --profiles-dir ../../ --profile tech_intel

dbt-docs-catalyst:
	@echo "📖 Generating Catalyst dbt documentation..."
	cd analytics/dbt_catalyst && uv run dbt docs generate --profiles-dir ../../ --profile tech_intel
	cd analytics/dbt_catalyst && uv run dbt docs serve --port 8081 --profiles-dir ../../ --profile tech_intel

dbt-clean:
	@echo "🧹 Cleaning dbt artifacts..."
	cd analytics/dbt_github && uv run dbt clean --profiles-dir ../../ --profile tech_intel
	cd analytics/dbt_catalyst && uv run dbt clean --profiles-dir ../../ --profile tech_intel

analytics-full: setup-unified dbt-run-all
	@echo "🎯 Full analytics pipeline completed!"
	@echo "📊 Single unified database ready with:"
	@echo "  📊 Raw: GitHub + Catalyst source data"
	@echo "  🔗 Bronze: Staging layer models"
	@echo "  🥈 Silver: Cleaned and transformed data"
	@echo "  🥇 Gold: Business-ready analytics and insights"

# Cloud-native development commands
run-local-lido:
	@echo "🚀 Running Lido pipeline locally..."
	uv run python scripts/run_local_lido.py

run-local-lido-sample:
	@echo "🚀 Running Lido pipeline locally (sample data)..."
	uv run python scripts/run_local_lido.py --sample

# Container development
docker-build-lido:
	@echo "🐳 Building Lido container..."
	docker build -f load/lido/Dockerfile -t cardano-insights-lido .

docker-build-dbt:
	@echo "🐳 Building dbt container..."
	docker build -f transform/Dockerfile -t cardano-insights-dbt .

docker-build-all: docker-build-lido docker-build-dbt
	@echo "✅ All containers built successfully"

# Terraform operations
tf-init:
	@echo "🏗️  Initializing Terraform..."
	cd infra && terraform init

tf-plan-dev:
	@echo "📋 Planning dev infrastructure..."
	cd infra && terraform plan -var-file="env/dev.tfvars"

tf-plan-prod:
	@echo "📋 Planning prod infrastructure..."
	cd infra && terraform plan -var-file="env/prod.tfvars"

# CI/CD style checks  
ci: clean install test-all
	@echo "🎯 CI pipeline completed successfully"

# Architecture documentation
docs-architecture:
	@echo "📖 Cloud architecture documentation:"
	@echo "  📄 CLOUD_ARCHITECTURE.md - Migration overview and structure"
	@echo "  📄 infra/README.md - Infrastructure deployment guide"
	@echo "  📄 load/lido/pipeline.py - Container-ready Lido ingestion"
	@echo "  📄 transform/ - dbt models for Athena/Glue"