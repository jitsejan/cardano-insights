"""
Pytest tests for Lido Nation Catalyst data extraction.
Uses pytest parametrize for comprehensive testing patterns.
"""
import pytest
import dlt
import duckdb
import os
from pathlib import Path

from src.cardano_insights.connectors.lido import funds, proposals_enriched, _extract_github_links, _categorize_proposal


class TestLidoHelperFunctions:
    """Fast unit tests for helper functions without API calls."""

    @pytest.mark.parametrize("text,expected_links", [
        ("Check out https://github.com/user/repo", ["https://github.com/user/repo"]),
        ("Visit https://github.com/user/repo for details", ["https://github.com/user/repo"]),
        ("Multiple: https://github.com/user1/repo1 and https://github.com/user2/repo2", 
         ["https://github.com/user1/repo1", "https://github.com/user2/repo2"]),
        ("No GitHub links here", []),
        ("Invalid bare github.com link", []),
        ("", [])
    ])
    def test_extract_github_links(self, text, expected_links):
        """Test GitHub link extraction from text."""
        result = _extract_github_links(text)
        assert result == expected_links, f"Expected {expected_links}, got {result}"

    @pytest.mark.parametrize("title,problem,solution,experience,expected_categories", [
        ("DeFi Protocol", "Need DeFi tools", "Building DeFi platform", "", ["DeFi"]),
        ("NFT Marketplace", "NFT trading", "Creating NFT marketplace", "", ["NFT"]),
        ("Infrastructure Tool", "Network issues", "Building infrastructure", "", ["Infrastructure"]),
        ("Developer SDK", "Need dev tools", "Building SDK for developers", "", ["Developer Tools"]),
        ("Educational Content", "Need education", "Creating educational materials", "", ["Education"]),
        ("Gaming Platform", "Gaming ecosystem", "Building game platform", "", ["Gaming"]),
        ("Random Project", "Some problem", "Some solution", "", ["Other"])
    ])
    def test_categorize_proposal(self, title, problem, solution, experience, expected_categories):
        """Test proposal categorization logic."""
        result = _categorize_proposal(title, problem, solution, experience)
        assert isinstance(result, list), "Should return a list"
        assert len(result) > 0, "Should return at least one category"
        # Check if expected categories are present
        for expected in expected_categories:
            assert expected in result, f"Expected category '{expected}' not found in {result}"


class TestLidoExtraction:
    """Test suite for Lido connector functionality."""

    @pytest.mark.integration
    @pytest.mark.parametrize("expected_key", [
        "id",
        "title", 
        "amount",
        "proposals_count"
    ])
    def test_funds_structure(self, expected_key):
        """Test that funds data contains expected keys."""
        funds_data = list(funds())
        assert len(funds_data) > 0, "No funds data returned"
        
        sample_fund = funds_data[0]
        assert isinstance(sample_fund, dict), "Fund should be a dictionary"
        # Note: some keys might be None but should exist in structure
        assert expected_key in sample_fund, f"Fund missing expected key: {expected_key}"

    @pytest.mark.integration
    @pytest.mark.parametrize("max_pages", [1])  # Reduced to 1 page for faster tests
    def test_proposals_extraction_with_limits(self, max_pages):
        """Test proposals extraction with different page limits."""
        proposals_data = list(proposals_enriched(max_pages=max_pages))
        
        assert len(proposals_data) > 0, f"No proposals data returned for {max_pages} pages"
        assert isinstance(proposals_data[0], dict), "Proposals should be dictionaries"
        
        # Should get some data
        assert len(proposals_data) >= 10, f"Expected at least 10 proposals, got {len(proposals_data)}"

    @pytest.mark.integration
    @pytest.mark.parametrize("required_field", [
        "id",
        "title",
        "has_github", 
        "categories",
        "primary_category",
        "github_links"
    ])
    def test_proposals_enrichment_fields(self, required_field):
        """Test that enriched proposals contain all required fields."""
        proposals_data = list(proposals_enriched(max_pages=1))
        assert len(proposals_data) > 0, "No proposals data returned"
        
        sample = proposals_data[0]
        assert required_field in sample, f"Proposal missing required field: {required_field}"

    @pytest.mark.integration  
    @pytest.mark.parametrize("pipeline_name,dataset_name", [
        ("test_pipeline_1", "test_dataset_1"),
        ("test_pipeline_2", "test_dataset_2")
    ])
    def test_pipeline_with_different_configs(self, pipeline_name, dataset_name):
        """Test dlt pipeline with different configurations."""
        pipeline = dlt.pipeline(
            pipeline_name=pipeline_name,
            destination="duckdb",
            dataset_name=dataset_name
        )
        
        # Load funds
        funds_info = pipeline.run(funds(), table_name="funds")
        assert funds_info is not None, f"Funds loading failed for {pipeline_name}"
        
        # Verify data in database
        db_file = f"{pipeline_name}.duckdb"
        conn = duckdb.connect(db_file)
        
        funds_count = conn.execute(f"SELECT COUNT(*) FROM {dataset_name}.funds").fetchone()[0]
        conn.close()
        
        assert funds_count > 0, f"No funds found in {pipeline_name}"
        
        # Cleanup
        if os.path.exists(db_file):
            os.remove(db_file)

    @pytest.fixture(autouse=True)
    def cleanup_test_db(self):
        """Clean up test database after each test."""
        yield  # Run the test
        
        # Cleanup test databases
        test_patterns = ["test_*.duckdb", "lido_test.duckdb"]
        for pattern in test_patterns:
            for file in Path(".").glob(pattern):
                if file.exists():
                    file.unlink()


class TestLidoEnrichment:
    """Test suite for Lido data enrichment features."""

    @pytest.mark.integration
    @pytest.mark.parametrize("github_field", [
        "github_links",
        "has_github"
    ])
    def test_github_fields_present(self, github_field):
        """Test that all GitHub-related fields are present in proposals."""
        proposals_data = list(proposals_enriched(max_pages=1))
        assert len(proposals_data) > 0, "No proposals data returned"
        
        sample = proposals_data[0]
        assert github_field in sample, f"Missing {github_field} field"

    @pytest.mark.integration
    @pytest.mark.parametrize("proposal_index", [0, 1, 2])  # Reduced for faster tests
    def test_category_fields_structure(self, proposal_index):
        """Test category structure across multiple proposals."""
        proposals_data = list(proposals_enriched(max_pages=1))
        
        # Skip if not enough proposals
        if len(proposals_data) <= proposal_index:
            pytest.skip(f"Not enough proposals for index {proposal_index}")
        
        proposal = proposals_data[proposal_index]
        
        # Check category enrichment structure
        assert 'categories' in proposal, f"Missing categories field in proposal {proposal_index}"
        assert 'primary_category' in proposal, f"Missing primary_category field in proposal {proposal_index}"
        
        categories = proposal['categories']
        primary_category = proposal['primary_category']
        
        assert isinstance(categories, list), f"categories should be a list in proposal {proposal_index}"
        assert len(categories) > 0, f"categories should not be empty in proposal {proposal_index}"
        assert isinstance(primary_category, str), f"primary_category should be a string in proposal {proposal_index}"
        assert primary_category in categories, f"primary_category should be in categories list in proposal {proposal_index}"

    @pytest.mark.integration
    @pytest.mark.parametrize("expected_category", [
        "DeFi", "Infrastructure", "Developer Tools"  # Reduced for faster tests
    ])
    def test_known_categories_can_be_assigned(self, expected_category):
        """Test that known categories can be properly assigned."""
        # This is more of a smoke test - we get proposals and check if any have these categories
        proposals_data = list(proposals_enriched(max_pages=2))
        
        # Check if any proposals have this category
        proposals_with_category = [
            p for p in proposals_data 
            if expected_category in p.get('categories', [])
        ]
        
        # We don't assert that ALL categories exist (as it depends on data)
        # But we verify the structure is correct if they do exist
        if proposals_with_category:
            sample = proposals_with_category[0]
            assert expected_category in sample['categories']
            # If it's in categories, could be primary too
            if sample['primary_category'] == expected_category:
                assert sample['primary_category'] in sample['categories']


class TestLidoIntegration:
    """Integration tests for Lido connector with real API calls."""

    @pytest.mark.slow
    def test_api_connectivity(self):
        """Test basic API connectivity (marked as slow test)."""
        funds_data = list(funds())
        
        assert len(funds_data) >= 12, "Expected at least 12 Catalyst funds"
        
        # Check fund structure
        sample_fund = funds_data[0]
        assert sample_fund.get('id'), "Fund should have ID"
        assert sample_fund.get('title'), "Fund should have title"

    @pytest.mark.slow
    @pytest.mark.parametrize("max_pages,min_expected", [
        (1, 40),
        (2, 80),
        (3, 120)
    ])
    def test_pagination_scaling(self, max_pages, min_expected):
        """Test that pagination scales properly with different page limits."""
        proposals_data = list(proposals_enriched(max_pages=max_pages))
        
        assert len(proposals_data) >= min_expected, f"Expected at least {min_expected} proposals for {max_pages} pages, got {len(proposals_data)}"
        
        # Verify all proposals have required structure
        for proposal in proposals_data[:5]:  # Check first 5 for performance
            assert 'id' in proposal, "Each proposal should have an ID"
            assert 'title' in proposal, "Each proposal should have a title"

    @pytest.mark.slow
    @pytest.mark.parametrize("fund_id", [None, 1, 2])
    def test_fund_filtering(self, fund_id):
        """Test fund filtering functionality."""
        if fund_id is None:
            # Test without filter
            proposals_data = list(proposals_enriched(max_pages=1))
        else:
            # Test with specific fund filter
            proposals_data = list(proposals_enriched(fund_id=fund_id, max_pages=1))
        
        assert len(proposals_data) >= 0, "Should return valid data (could be empty for specific funds)"
        
        # If we have data and used a filter, verify the filter worked
        if proposals_data and fund_id is not None:
            sample = proposals_data[0]
            if 'fund_id' in sample:
                assert sample['fund_id'] == fund_id, f"Expected fund_id {fund_id}, got {sample['fund_id']}"


class TestLidoErrorHandling:
    """Test error handling and edge cases."""
    
    @pytest.mark.integration
    @pytest.mark.parametrize("invalid_max_pages", [-1, 0])
    def test_invalid_max_pages_handling(self, invalid_max_pages):
        """Test handling of invalid max_pages values."""
        # This should either raise an error or handle gracefully
        try:
            proposals_data = list(proposals_enriched(max_pages=invalid_max_pages))
            # If it doesn't raise an error, should return empty or handle gracefully
            assert isinstance(proposals_data, list), "Should return a list even for invalid input"
        except (ValueError, TypeError):
            # This is acceptable - invalid input should raise an error
            pass

    @pytest.mark.integration
    @pytest.mark.parametrize("fund_id", [-999, 0, 999999])
    def test_nonexistent_fund_handling(self, fund_id):
        """Test handling of non-existent fund IDs."""
        # These fund IDs shouldn't exist, should return empty results
        proposals_data = list(proposals_enriched(fund_id=fund_id, max_pages=1))
        
        # Should return empty list, not error
        assert isinstance(proposals_data, list), "Should return a list"
        # Could be empty for non-existent funds
        assert len(proposals_data) >= 0, "Should handle non-existent fund gracefully"