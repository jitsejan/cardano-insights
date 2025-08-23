"""
Basic tests to verify test infrastructure and imports.
"""
import pytest
from src.cardano_insights.connectors import lido


def test_import_lido_connector():
    """Test that we can import the lido connector."""
    assert hasattr(lido, 'funds')
    assert hasattr(lido, 'proposals_enriched')
    assert callable(lido.funds)
    assert callable(lido.proposals_enriched)


def test_sample_fixtures(sample_fund, sample_proposal):
    """Test that our sample fixtures work correctly."""
    # Test sample fund
    assert sample_fund["id"] == 1
    assert sample_fund["title"] == "Fund 1"
    assert isinstance(sample_fund["funding_available"], int)
    
    # Test sample proposal
    assert sample_proposal["id"] == 1
    assert sample_proposal["title"] == "Test Proposal"
    assert sample_proposal["has_github"] is True
    assert len(sample_proposal["github_links"]) > 0
    assert len(sample_proposal["categories"]) > 0


def test_pytest_markers():
    """Test that our pytest markers are working."""
    # This test should always pass
    assert True
    
    
@pytest.mark.slow
def test_slow_marker():
    """Test the slow marker (should be skipped in fast runs)."""
    # This test should be skipped when running with -m "not slow"
    assert True