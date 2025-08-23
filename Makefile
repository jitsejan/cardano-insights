# Cardano Insights - Development Commands

.PHONY: help install test test-fast test-all test-lido test-basic test-cov clean lint format check

# Default target
help:
	@echo "🧪 Cardano Insights - Available Commands"
	@echo "======================================"
	@echo "Setup:"
	@echo "  install     - Install dependencies including test dependencies"
	@echo "  install-dev - Install development dependencies"
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