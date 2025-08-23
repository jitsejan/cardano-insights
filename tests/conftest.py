"""
Pytest configuration and shared fixtures for cardano-insights tests.
"""
import pytest
import os
from pathlib import Path


@pytest.fixture(scope="session", autouse=True)
def test_environment():
    """Set up test environment variables and cleanup."""
    # Set test environment
    os.environ["TESTING"] = "1"
    
    yield
    
    # Cleanup test databases after all tests
    test_db_patterns = ["*test*.duckdb", "lido_test.duckdb"]
    for pattern in test_db_patterns:
        for db_file in Path(".").glob(pattern):
            if db_file.exists():
                db_file.unlink()


@pytest.fixture
def sample_fund():
    """Sample fund data for testing."""
    return {
        "id": 1,
        "title": "Fund 1",
        "status": "completed",
        "funding_available": 500000,
        "proposals_count": 100
    }


@pytest.fixture  
def sample_proposal():
    """Sample proposal data for testing."""
    return {
        "id": 1,
        "title": "Test Proposal",
        "problem": "This is a test problem statement",
        "solution": "This is a test solution with github.com/test/repo link",
        "amount_requested": 10000,
        "amount_received": 8000,
        "has_github": True,
        "github_links": ["https://github.com/test/repo"],
        "categories": ["Developer Tools", "Infrastructure"],
        "primary_category": "Developer Tools"
    }