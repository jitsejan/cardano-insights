# Cardano Insights - Development Commands

.PHONY: help install test test-fast test-all test-lido test-basic test-cov clean lint format check extract extract-sample extract-full data-status

# Default target
help:
	@echo "🧪 Cardano Insights - Available Commands"
	@echo "======================================"
	@echo "Setup:"
	@echo "  install     - Install dependencies including test dependencies"
	@echo "  install-dev - Install development dependencies"
	@echo ""
	@echo "Data Extraction:"
	@echo "  extract       - Run sample data extraction (quick test)"
	@echo "  extract-full  - Run full Catalyst ecosystem extraction"
	@echo "  data-status   - Show current database status and record counts"
	@echo ""
	@echo "Testing:"
	@echo "  test        - Run fast tests (default, skips slow API tests)"
	@echo "  test-all    - Run all tests including slow API tests"
	@echo "  test-lido   - Run only Lido connector tests"
	@echo "  test-basic  - Run basic infrastructure tests"
	@echo "  test-cov    - Run tests with coverage report"
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
	uv run python -m pytest tests/ -v -m "not slow"

test-all:
	@echo "🚀 Running all tests (including slow API tests)..."
	uv run python -m pytest tests/ -v

test-lido:
	@echo "🚀 Running Lido connector tests..."
	uv run python -m pytest tests/connectors/test_lido.py -v

test-basic:
	@echo "🚀 Running basic infrastructure tests..."
	uv run python -m pytest tests/test_basic.py -v

test-cov:
	@echo "🚀 Running tests with coverage report..."
	uv run python -m pytest tests/ --cov=src --cov-report=html --cov-report=term-missing

# Data Extraction
extract:
	@echo "🔍 Running sample data extraction (2 pages max)..."
	uv run python -c "import dlt; from src.cardano_insights.connectors.lido import funds, proposals_enriched; pipeline = dlt.pipeline('sample_pipeline', destination='duckdb', dataset_name='catalyst_sample'); print('Loading funds...'); pipeline.run(funds(), table_name='funds'); print('Loading sample proposals...'); pipeline.run(proposals_enriched(max_pages=2), table_name='proposals_sample')"
	@echo "✅ Sample extraction completed - check sample_pipeline.duckdb"

extract-full:
	@echo "🚀 Running FULL Catalyst ecosystem extraction..."
	@echo "⚠️  This will take several minutes and download ~10k proposals"
	@read -p "Continue? [y/N] " confirm && [ "$$confirm" = "y" ] || exit 1
	uv run python -c "import dlt; from src.cardano_insights.connectors.lido import funds, proposals_enriched; pipeline = dlt.pipeline('full_pipeline', destination='duckdb', dataset_name='catalyst_ecosystem'); print('Loading all funds...'); pipeline.run(funds(), table_name='funds'); print('Loading ALL proposals (this will take time)...'); pipeline.run(proposals_enriched(), table_name='proposals_enriched')"
	@echo "✅ Full extraction completed - check full_pipeline.duckdb"

data-status:
	@echo "📊 Database Status Report"
	@echo "======================="
	@if [ -f "catalyst_complete.duckdb" ]; then \
		echo "📁 catalyst_complete.duckdb (existing complete dataset):"; \
		uv run python -c "import duckdb; conn = duckdb.connect('catalyst_complete.duckdb', read_only=True); funds = conn.execute('SELECT COUNT(*) FROM catalyst_ecosystem.funds').fetchone()[0]; proposals = conn.execute('SELECT COUNT(*) FROM catalyst_ecosystem.proposals_enriched').fetchone()[0]; funded = conn.execute('SELECT COUNT(*) FROM catalyst_ecosystem.proposals_enriched WHERE amount_received > 0').fetchone()[0]; github = conn.execute('SELECT COUNT(*) FROM catalyst_ecosystem.proposals_enriched WHERE has_github = true').fetchone()[0]; print(f'   - Funds: {funds:,}'); print(f'   - Proposals: {proposals:,}'); print(f'   - Funded: {funded:,}'); print(f'   - With GitHub: {github:,}'); conn.close()"; \
	else \
		echo "❌ catalyst_complete.duckdb not found"; \
	fi
	@if [ -f "sample_pipeline.duckdb" ]; then \
		echo "📁 sample_pipeline.duckdb (sample dataset):"; \
		uv run python -c "import duckdb; conn = duckdb.connect('sample_pipeline.duckdb', read_only=True); funds = conn.execute('SELECT COUNT(*) FROM catalyst_sample.funds').fetchone()[0]; proposals = conn.execute('SELECT COUNT(*) FROM catalyst_sample.proposals_sample').fetchone()[0]; print(f'   - Funds: {funds:,}'); print(f'   - Sample Proposals: {proposals:,}'); conn.close()"; \
	else \
		echo "ℹ️  No sample database (run 'make extract' to create)"; \
	fi
	@if [ -f "full_pipeline.duckdb" ]; then \
		echo "📁 full_pipeline.duckdb (full extraction):"; \
		uv run python -c "import duckdb; conn = duckdb.connect('full_pipeline.duckdb', read_only=True); funds = conn.execute('SELECT COUNT(*) FROM catalyst_ecosystem.funds').fetchone()[0]; proposals = conn.execute('SELECT COUNT(*) FROM catalyst_ecosystem.proposals_enriched').fetchone()[0]; funded = conn.execute('SELECT COUNT(*) FROM catalyst_ecosystem.proposals_enriched WHERE amount_received > 0').fetchone()[0]; github = conn.execute('SELECT COUNT(*) FROM catalyst_ecosystem.proposals_enriched WHERE has_github = true').fetchone()[0]; print(f'   - Funds: {funds:,}'); print(f'   - Proposals: {proposals:,}'); print(f'   - Funded: {funded:,}'); print(f'   - With GitHub: {github:,}'); conn.close()"; \
	else \
		echo "ℹ️  No full extraction database (run 'make extract-full' to create)"; \
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

# CI/CD style checks  
ci: clean install test-all
	@echo "🎯 CI pipeline completed successfully"