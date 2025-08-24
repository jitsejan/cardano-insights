"""
Basic tests to verify test infrastructure and imports.
"""
import pytest
from src.cardano_insights.connectors import lido


def test_import_lido_connector():
    """Test that we can import the lido connector."""
    assert hasattr(lido, 'funds')
    assert hasattr(lido, 'proposals_raw')
    assert callable(lido.funds)
    assert callable(lido.proposals_raw)


def test_sample_fixtures(sample_fund, sample_proposal):
    """Test that our sample fixtures work correctly."""
    # Test sample fund structure - values vary based on parametrization
    assert "id" in sample_fund
    assert "title" in sample_fund 
    assert isinstance(sample_fund["funding_available"], int)
    
    # Test sample proposal structure - values vary based on parametrization  
    assert "id" in sample_proposal
    assert "title" in sample_proposal
    assert "has_github" in sample_proposal
    assert "github_links" in sample_proposal
    assert isinstance(sample_proposal["github_links"], list)
    assert "categories" in sample_proposal
    assert isinstance(sample_proposal["categories"], list)


def test_pytest_markers():
    """Test that our pytest markers are working."""
    # This test should always pass
    assert True
    
    
@pytest.mark.slow
def test_slow_marker():
    """Test the slow marker (should be skipped in fast runs)."""
    # This test should be skipped when running with -m "not slow"
    assert True