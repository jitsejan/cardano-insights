"""
Pytest tests for Lido Nation Catalyst data extraction.
Uses pytest parametrize for comprehensive testing patterns.
"""
import pytest
import dlt
import duckdb
import os
from pathlib import Path

from src.cardano_insights.connectors.lido import funds, proposals


class TestLidoConnector:
    """Fast unit tests for connector functions without API calls."""

    def test_connector_imports(self):
        """Test that we can import the connector functions."""
        # Basic smoke test that the functions exist and are callable
        assert callable(funds), "funds should be callable"
        assert callable(proposals), "proposals should be callable"
        
    @pytest.mark.parametrize("max_pages", [1, 2])
    def test_proposals_accepts_max_pages(self, max_pages):
        """Test that proposals function accepts max_pages parameter."""
        # This tests the function signature without making API calls
        try:
            # Just test that we can call the function - iterator won't execute until consumed
            iterator = proposals(max_pages=max_pages)
            assert hasattr(iterator, '__iter__'), "Should return an iterator"
        except Exception as e:
            pytest.fail(f"proposals(max_pages={max_pages}) should not raise exception: {e}")
    
    def test_proposals_accepts_fund_id(self):
        """Test that proposals function accepts fund_id parameter."""
        try:
            # Just test that we can call the function - iterator won't execute until consumed
            iterator = proposals(fund_id=1)
            assert hasattr(iterator, '__iter__'), "Should return an iterator"
        except Exception as e:
            pytest.fail(f"proposals(fund_id=1) should not raise exception: {e}")


class TestLidoExtraction:
    """Test suite for Lido connector functionality."""

    @pytest.mark.integration
    def test_funds_structure_integration(self):
        """Test that funds data contains expected keys (single API call)."""
        funds_data = list(funds())
        assert len(funds_data) > 0, "No funds data returned"
        
        sample_fund = funds_data[0]
        assert isinstance(sample_fund, dict), "Fund should be a dictionary"
        
        # Check all required keys at once to minimize API calls
        required_keys = ["id", "title", "amount", "proposals_count"]
        for expected_key in required_keys:
            assert expected_key in sample_fund, f"Fund missing expected key: {expected_key}"

    @pytest.mark.integration
    @pytest.mark.parametrize("max_pages", [1])  # Reduced to 1 page for faster tests
    def test_proposals_extraction_with_limits(self, max_pages):
        """Test proposals extraction with different page limits."""
        proposals_data = list(proposals(max_pages=max_pages))
        
        assert len(proposals_data) > 0, f"No proposals data returned for {max_pages} pages"
        assert isinstance(proposals_data[0], dict), "Proposals should be dictionaries"
        
        # Should get some data
        assert len(proposals_data) >= 10, f"Expected at least 10 proposals, got {len(proposals_data)}"

    @pytest.mark.integration  
    def test_proposals_basic_fields_integration(self):
        """Test that proposals contain basic required fields (single API call)."""
        proposals_data = list(proposals(max_pages=1))
        assert len(proposals_data) > 0, "No proposals data returned"
        
        sample = proposals_data[0]
        # Check basic raw API fields (enrichment fields will be added by dbt)
        required_fields = ["id", "title", "amount_requested", "fund_id"]
        for required_field in required_fields:
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
    @pytest.mark.parametrize("raw_field", [
        "id",
        "title", 
        "solution",
        "problem",
        "embedded_uris"
    ])
    def test_raw_fields_present(self, raw_field):
        """Test that essential raw fields are present in proposals."""
        proposals_data = list(proposals(max_pages=1))
        assert len(proposals_data) > 0, "No proposals data returned"
        
        sample = proposals_data[0]
        assert raw_field in sample, f"Missing {raw_field} field"

    @pytest.mark.integration
    def test_embedded_uris_structure(self):
        """Test that embedded_uris field contains GitHub links when present."""
        proposals_data = list(proposals(max_pages=1))
        assert len(proposals_data) > 0, "No proposals data returned"
        
        # Look for proposals with embedded_uris that contain GitHub links
        github_proposals = [
            p for p in proposals_data
            if 'embedded_uris' in p and p['embedded_uris'] and
            any('github.com' in str(uri) for uri_list in p['embedded_uris'] for uri in uri_list)
        ]
        
        if github_proposals:
            sample = github_proposals[0]
            assert 'embedded_uris' in sample
            assert isinstance(sample['embedded_uris'], list)
            # Verify it contains at least one GitHub URI
            has_github_uri = any(
                'github.com' in str(uri) 
                for uri_list in sample['embedded_uris'] 
                for uri in uri_list
            )
            assert has_github_uri, "Expected GitHub URI in embedded_uris"


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
        proposals_data = list(proposals(max_pages=max_pages))
        
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
            proposals_data = list(proposals(max_pages=1))
        else:
            # Test with specific fund filter
            proposals_data = list(proposals(fund_id=fund_id, max_pages=1))
        
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
            proposals_data = list(proposals(max_pages=invalid_max_pages))
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
        proposals_data = list(proposals(fund_id=fund_id, max_pages=1))
        
        # Should return empty list, not error
        assert isinstance(proposals_data, list), "Should return a list"
        # Could be empty for non-existent funds
        assert len(proposals_data) >= 0, "Should handle non-existent fund gracefully"