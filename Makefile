# Cardano Insights - Development Commands

.PHONY: help install test test-fast test-all test-lido test-basic test-cov clean lint format check extract-lido extract-lido-full data-status

# Default target
help:
	@echo "🧪 Cardano Insights - Available Commands"
	@echo "======================================"
	@echo "Setup:"
	@echo "  install     - Install dependencies including test dependencies"
	@echo "  install-dev - Install development dependencies"
	@echo ""
	@echo "Data Extraction:"
	@echo "  extract-lido      - Run sample Lido Catalyst extraction (quick test)"
	@echo "  extract-lido-full - Run full Lido Catalyst ecosystem extraction"
	@echo "  data-status       - Show current database status and record counts"
	@echo ""
	@echo "dbt Analytics:"
	@echo "  dbt-run          - Run all dbt models (bronze → silver → gold)"
	@echo "  dbt-test         - Run dbt tests on models"
	@echo "  dbt-docs         - Generate and serve dbt documentation"
	@echo "  dbt-clean        - Clean dbt artifacts"
	@echo "  analytics-full   - Full pipeline: extract-lido-full + dbt-run"
	@echo ""
	@echo "Testing:"
	@echo "  test           - Run fast unit tests (no API calls, ~0.15s)"
	@echo "  test-all       - Run all tests including slow API tests"
	@echo "  test-lido      - Run only Lido connector unit tests (fast)"
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

test-integration:
	@echo "🚀 Running integration tests (makes API calls)..."
	uv run python -m pytest tests/ -v -m "integration"

test-basic:
	@echo "🚀 Running basic infrastructure tests..."
	uv run python -m pytest tests/test_basic.py -v

test-cov:
	@echo "🚀 Running tests with coverage report..."
	uv run python -m pytest tests/ --cov=src --cov-report=html --cov-report=term-missing

# Data Extraction - Lido Catalyst Explorer API (Raw for dbt)
extract-lido:
	@echo "🔍 Running sample Lido Catalyst extraction (2 pages max)..."
	uv run python -c "import dlt; from src.cardano_insights.connectors.lido_raw import funds, proposals_raw; pipeline = dlt.pipeline('lido', destination='duckdb', dataset_name='lido'); print('Loading funds...'); pipeline.run(funds(), table_name='funds'); print('Loading sample proposals...'); pipeline.run(proposals_raw(max_pages=2), table_name='proposals_enriched')"
	@echo "✅ Lido sample extraction completed - check lido.duckdb"

extract-lido-full:
	@echo "🚀 Running FULL Lido Catalyst ecosystem extraction..."
	@echo "⚠️  This will take several minutes and download ~10k proposals"
	@read -p "Continue? [y/N] " confirm && [ "$$confirm" = "y" ] || exit 1
	uv run python -c "import dlt; from src.cardano_insights.connectors.lido_raw import funds, proposals_raw; pipeline = dlt.pipeline('lido', destination='duckdb', dataset_name='lido'); print('Loading all funds...'); pipeline.run(funds(), table_name='funds'); print('Loading ALL proposals (this will take time)...'); pipeline.run(proposals_raw(), table_name='proposals_enriched')"
	@echo "✅ Lido full extraction completed - ready for dbt processing"

# Data Extraction - Future sources (examples for when we add more)
# extract-github:
#	@echo "🔍 Running GitHub repository extraction..."
# extract-cardanoscan:
#	@echo "🔍 Running CardanoScan data extraction..."

data-status:
	@echo "📊 Database Status Report"
	@echo "======================="
	@if [ -f "catalyst_complete.duckdb" ]; then \
		echo "📁 catalyst_complete.duckdb (existing complete dataset):"; \
		uv run python -c "import duckdb; conn = duckdb.connect('catalyst_complete.duckdb', read_only=True); funds = conn.execute('SELECT COUNT(*) FROM catalyst_ecosystem.funds').fetchone()[0]; proposals = conn.execute('SELECT COUNT(*) FROM catalyst_ecosystem.proposals_enriched').fetchone()[0]; funded = conn.execute('SELECT COUNT(*) FROM catalyst_ecosystem.proposals_enriched WHERE amount_received > 0').fetchone()[0]; github = conn.execute('SELECT COUNT(*) FROM catalyst_ecosystem.proposals_enriched WHERE has_github = true').fetchone()[0]; print(f'   - Funds: {funds:,}'); print(f'   - Proposals: {proposals:,}'); print(f'   - Funded: {funded:,}'); print(f'   - With GitHub: {github:,}'); conn.close()"; \
	else \
		echo "❌ catalyst_complete.duckdb not found"; \
	fi
	@if [ -f "lido_sample.duckdb" ]; then \
		echo "📁 lido_sample.duckdb (Lido sample dataset):"; \
		uv run python -c "import duckdb; conn = duckdb.connect('lido_sample.duckdb', read_only=True); funds = conn.execute('SELECT COUNT(*) FROM catalyst_lido_sample.funds').fetchone()[0]; proposals = conn.execute('SELECT COUNT(*) FROM catalyst_lido_sample.proposals_sample').fetchone()[0]; print(f'   - Funds: {funds:,}'); print(f'   - Sample Proposals: {proposals:,}'); conn.close()"; \
	else \
		echo "ℹ️  No Lido sample database (run 'make extract-lido' to create)"; \
	fi
	@if [ -f "lido_full.duckdb" ]; then \
		echo "📁 lido_full.duckdb (Lido full extraction):"; \
		uv run python -c "import duckdb; conn = duckdb.connect('lido_full.duckdb', read_only=True); funds = conn.execute('SELECT COUNT(*) FROM catalyst_lido_full.funds').fetchone()[0]; proposals = conn.execute('SELECT COUNT(*) FROM catalyst_lido_full.proposals_enriched').fetchone()[0]; funded = conn.execute('SELECT COUNT(*) FROM catalyst_lido_full.proposals_enriched WHERE amount_received > 0').fetchone()[0]; github = conn.execute('SELECT COUNT(*) FROM catalyst_lido_full.proposals_enriched WHERE has_github = true').fetchone()[0]; print(f'   - Funds: {funds:,}'); print(f'   - Proposals: {proposals:,}'); print(f'   - Funded: {funded:,}'); print(f'   - With GitHub: {github:,}'); conn.close()"; \
	else \
		echo "ℹ️  No Lido full extraction database (run 'make extract-lido-full' to create)"; \
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
	@echo "🧹 Cleaning up test artifacts..."
	find . -name "*.duckdb" -type f -delete
	find . -name "*.duckdb.wal" -type f -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete
	find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name "htmlcov" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name ".coverage" -delete 2>/dev/null || true
	@echo "✅ Cleanup completed"

# Development workflow
dev-setup: install
	@echo "🛠️  Development environment ready!"
	@echo "Run 'make test' to verify everything works"

# dbt Analytics Commands
dbt-run:
	@echo "🔄 Running dbt models (bronze → silver → gold)..."
	uv run dbt run

dbt-test:
	@echo "🧪 Running dbt tests..."
	uv run dbt test

dbt-docs:
	@echo "📖 Generating and serving dbt documentation..."
	uv run dbt docs generate
	uv run dbt docs serve --port 8080

dbt-clean:
	@echo "🧹 Cleaning dbt artifacts..."
	uv run dbt clean

analytics-full: extract-lido-full dbt-run
	@echo "🎯 Full analytics pipeline completed!"
	@echo "📊 Check your database for:"
	@echo "  - Bronze: stg_funds, stg_proposals"
	@echo "  - Silver: proposals_enriched"  
	@echo "  - Gold: funded_projects_summary, wallet_ecosystem_analysis, lace_competitive_landscape"

# CI/CD style checks  
ci: clean install test-all
	@echo "🎯 CI pipeline completed successfully"