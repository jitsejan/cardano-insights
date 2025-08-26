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
	@echo "  extract-github     - Run GitHub repository extraction (sample)"
	@echo "  extract-lido       - Run sample Lido Catalyst extraction"
	@echo "  extract-lido-full  - Run full Lido Catalyst ecosystem extraction"
	@echo "  merge-databases    - Merge source DBs into unified tech_intel.duckdb"
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
	@echo "  analytics-full    - Full pipeline: extract + merge + dbt-run-all"
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

# Data Extraction - GitHub API
extract-github:
	@echo "🔍 Running GitHub repository extraction..."
	uv run python -c "import dlt; from src.cardano_insights.connectors.github import repositories, pull_requests, releases; pipeline = dlt.pipeline(pipeline_name='github_data', destination='duckdb', dataset_name='github_raw'); print('Loading repositories...'); pipeline.run(repositories(repos=['cardano-foundation/cardano-wallet', 'input-output-hk/cardano-node']), table_name='repositories'); print('Loading pull requests...'); pipeline.run(pull_requests(repos=['cardano-foundation/cardano-wallet', 'input-output-hk/cardano-node'], max_per_repo=50), table_name='pull_requests'); print('Loading releases...'); pipeline.run(releases(repos=['cardano-foundation/cardano-wallet', 'input-output-hk/cardano-node'], max_per_repo=10), table_name='releases')"
	@echo "✅ GitHub extraction completed - check github_data.duckdb"

# Data Extraction - Lido Catalyst Explorer API  
extract-lido:
	@echo "🔍 Running sample Lido Catalyst extraction (2 pages max)..."
	uv run python -c "import dlt; from src.cardano_insights.connectors.lido import funds, proposals; pipeline = dlt.pipeline(pipeline_name='cardano_data', destination='duckdb', dataset_name='lido_raw'); print('Loading funds...'); pipeline.run(funds(), table_name='funds'); print('Loading sample proposals...'); pipeline.run(proposals(max_pages=2), table_name='proposals')"
	@echo "✅ Lido sample extraction completed - check cardano_data.duckdb"

extract-lido-full:
	@echo "🚀 Running FULL Lido Catalyst ecosystem extraction..."
	@echo "⚠️  This will take several minutes and download ~10k proposals"
	@read -p "Continue? [y/N] " confirm && [ "$$confirm" = "y" ] || exit 1
	uv run python -c "import dlt; from src.cardano_insights.connectors.lido import funds, proposals; pipeline = dlt.pipeline(pipeline_name='cardano_data', destination='duckdb', dataset_name='lido_raw'); print('Loading all funds...'); pipeline.run(funds(), table_name='funds'); print('Loading ALL proposals (this will take time)...'); pipeline.run(proposals(), table_name='proposals')"
	@echo "✅ Lido full extraction completed - check cardano_data.duckdb"

# Unified Database Setup
merge-databases:
	@echo "🔗 Merging source databases into unified tech_intel.duckdb..."
	@if [ ! -f "github_data.duckdb" ] || [ ! -f "cardano_data.duckdb" ]; then \
		echo "❌ Source databases not found. Run 'make extract-github' and 'make extract-lido' first."; \
		exit 1; \
	fi
	duckdb -f scripts/merge_duckdb.sql
	@echo "✅ Unified database created - ready for dbt analytics"

setup-unified: extract-github extract-lido merge-databases
	@echo "🎯 Unified tech intelligence platform setup completed!"
	@echo "📊 You can now run 'make dbt-run-all' for analytics"

data-status:
	@echo "📊 Unified Tech Intelligence Database Status"
	@echo "============================================"
	@if [ -f "tech_intel.duckdb" ]; then \
		echo "🎯 tech_intel.duckdb (unified analytics database):"; \
		uv run python -c "import duckdb; conn = duckdb.connect('tech_intel.duckdb', read_only=True); github_repos = conn.execute('SELECT COUNT(*) FROM bronze.github_repos').fetchone()[0]; github_prs = conn.execute('SELECT COUNT(*) FROM bronze.github_prs').fetchone()[0]; github_releases = conn.execute('SELECT COUNT(*) FROM bronze.github_releases').fetchone()[0]; catalyst_funds = conn.execute('SELECT COUNT(*) FROM bronze.catalyst_funds').fetchone()[0]; catalyst_proposals = conn.execute('SELECT COUNT(*) FROM bronze.catalyst_proposals').fetchone()[0]; print(f'   📊 GitHub Data:'); print(f'     - Repositories: {github_repos:,}'); print(f'     - Pull Requests: {github_prs:,}'); print(f'     - Releases: {github_releases:,}'); print(f'   🏛️  Catalyst Data:'); print(f'     - Funds: {catalyst_funds:,}'); print(f'     - Proposals: {catalyst_proposals:,}'); conn.close()"; \
	else \
		echo "❌ tech_intel.duckdb not found - run 'make setup-unified' to create"; \
	fi
	@echo ""
	@if [ -f "github_data.duckdb" ]; then \
		echo "📁 github_data.duckdb (GitHub source data):"; \
		uv run python -c "import duckdb; conn = duckdb.connect('github_data.duckdb', read_only=True); repos = conn.execute('SELECT COUNT(*) FROM github_raw.repositories').fetchone()[0]; prs = conn.execute('SELECT COUNT(*) FROM github_raw.pull_requests').fetchone()[0]; releases = conn.execute('SELECT COUNT(*) FROM github_raw.releases').fetchone()[0]; print(f'   - Repositories: {repos:,}'); print(f'   - Pull Requests: {prs:,}'); print(f'   - Releases: {releases:,}'); conn.close()"; \
	else \
		echo "ℹ️  No GitHub database (run 'make extract-github' to create)"; \
	fi
	@if [ -f "cardano_data.duckdb" ]; then \
		echo "📁 cardano_data.duckdb (Cardano/Catalyst source data):"; \
		uv run python -c "import duckdb; conn = duckdb.connect('cardano_data.duckdb', read_only=True); funds = conn.execute('SELECT COUNT(*) FROM lido_raw.funds').fetchone()[0]; proposals = conn.execute('SELECT COUNT(*) FROM lido_raw.proposals').fetchone()[0]; print(f'   - Funds: {funds:,}'); print(f'   - Proposals: {proposals:,}'); conn.close()"; \
	else \
		echo "ℹ️  No Cardano database (run 'make extract-lido' or 'make extract-lido-full' to create)"; \
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
	cd analytics/dbt_github && uv run dbt run --profiles-dir ../../ --profile tech_intel

dbt-run-catalyst:
	@echo "🔄 Running Catalyst dbt models (bronze → silver → gold)..."
	cd analytics/dbt_catalyst && uv run dbt run --profiles-dir ../../ --profile tech_intel

dbt-run-all: dbt-run-github dbt-run-catalyst
	@echo "✅ All dbt models completed (GitHub + Catalyst)!"

dbt-test:
	@echo "🧪 Running dbt tests..."
	cd analytics/dbt_github && uv run dbt test --profiles-dir ../../ --profile tech_intel
	cd analytics/dbt_catalyst && uv run dbt test --profiles-dir ../../ --profile tech_intel

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
	@echo "📊 Unified tech intelligence database ready with:"
	@echo "  🔗 Bronze: Unified source data (GitHub + Catalyst)"
	@echo "  🥈 Silver: Cleaned and transformed data"
	@echo "  🥇 Gold: Business-ready analytics and insights"

# CI/CD style checks  
ci: clean install test-all
	@echo "🎯 CI pipeline completed successfully"