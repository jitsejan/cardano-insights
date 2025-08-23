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


# Parametrized fixtures for different fund scenarios
@pytest.fixture(params=[
    {"id": 1, "title": "Fund 1", "status": "completed", "funding_available": 500000},
    {"id": 2, "title": "Fund 2", "status": "active", "funding_available": 1000000},
    {"id": 3, "title": "Fund 3", "status": "upcoming", "funding_available": 1500000}
])
def sample_fund(request):
    """Parametrized sample fund data for testing different fund scenarios."""
    fund_data = request.param.copy()
    fund_data["proposals_count"] = 100  # Add common field
    return fund_data


@pytest.fixture(params=[
    # Proposal with GitHub
    {
        "id": 1,
        "title": "DeFi Proposal with GitHub", 
        "problem": "Need better DeFi tools",
        "solution": "Building DeFi platform with github.com/test/defi-repo",
        "amount_requested": 50000,
        "amount_received": 45000,
        "has_github": True,
        "github_links": ["https://github.com/test/defi-repo"],
        "categories": ["DeFi", "Developer Tools"],
        "primary_category": "DeFi"
    },
    # Proposal without GitHub
    {
        "id": 2,
        "title": "Education Proposal",
        "problem": "Need better education",
        "solution": "Creating educational content",
        "amount_requested": 20000,
        "amount_received": 0,
        "has_github": False,
        "github_links": [],
        "categories": ["Education"],
        "primary_category": "Education"
    },
    # Infrastructure proposal
    {
        "id": 3,
        "title": "Infrastructure Tool",
        "problem": "Network needs improvement",
        "solution": "Building infrastructure tools",
        "amount_requested": 75000,
        "amount_received": 70000,
        "has_github": True,
        "github_links": ["https://github.com/test/infra-tool"],
        "categories": ["Infrastructure", "Developer Tools"],
        "primary_category": "Infrastructure"
    }
])
def sample_proposal(request):
    """Parametrized sample proposal data covering different scenarios."""
    return request.param


@pytest.fixture(params=["DeFi", "NFT", "Infrastructure", "Developer Tools", "Education"])
def sample_category(request):
    """Parametrized fixture for testing different proposal categories."""
    return request.param


@pytest.fixture(params=[
    {"pipeline_name": "test_pipeline_a", "dataset_name": "test_dataset_a"},
    {"pipeline_name": "test_pipeline_b", "dataset_name": "test_dataset_b"}
])
def pipeline_config(request):
    """Parametrized pipeline configuration for testing different setups."""
    return request.param


@pytest.fixture
def github_proposal():
    """Specific fixture for proposals with GitHub links."""
    return {
        "id": 100,
        "title": "Open Source Project",
        "problem": "Need open source tools",
        "solution": "Building at https://github.com/test/awesome-project",
        "has_github": True,
        "github_links": [
            "https://github.com/test/awesome-project",
            "https://github.com/test/helper-lib"
        ],
        "categories": ["Developer Tools", "Infrastructure"],
        "primary_category": "Developer Tools"
    }


@pytest.fixture
def non_github_proposal():
    """Specific fixture for proposals without GitHub links."""
    return {
        "id": 101,
        "title": "Community Initiative",
        "problem": "Need community engagement",
        "solution": "Organizing community events",
        "has_github": False,
        "github_links": [],
        "categories": ["Social", "Education"],
        "primary_category": "Social"
    }