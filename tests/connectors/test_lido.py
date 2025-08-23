"""
Pytest tests for Lido Nation Catalyst data extraction.
Tests both funds and proposals_enriched resources.
"""
import pytest
import dlt
import duckdb
import os
from pathlib import Path

from src.cardano_insights.connectors.lido import funds, proposals_enriched


class TestLidoExtraction:
    """Test suite for Lido connector functionality."""

    def test_funds_extraction(self):
        """Test funds extraction from Lido API."""
        # Test the funds resource
        funds_data = list(funds())
        
        # Assertions
        assert len(funds_data) > 0, "No funds data returned"
        assert isinstance(funds_data[0], dict), "Funds data should be dictionaries"
        
        # Check for expected fund structure
        sample_fund = funds_data[0]
        expected_keys = ['id', 'title']
        for key in expected_keys:
            assert key in sample_fund, f"Fund missing expected key: {key}"
        
        print(f"✅ Funds extraction successful: {len(funds_data)} funds found")

    def test_proposals_extraction(self):
        """Test proposals extraction with limited data."""
        # Test proposals with max_pages=1 to avoid long extraction
        proposals_data = list(proposals_enriched(max_pages=1))
        
        # Assertions
        assert len(proposals_data) > 0, "No proposals data returned"
        assert isinstance(proposals_data[0], dict), "Proposals data should be dictionaries"
        
        # Show sample proposal structure
        sample = proposals_data[0]
        expected_keys = ['id', 'title', 'has_github', 'categories', 'primary_category']
        for key in expected_keys:
            assert key in sample, f"Proposal missing expected key: {key}"
        
        # Check for enrichment features
        has_github_enrichment = any(p.get('has_github') is not None for p in proposals_data[:5])
        has_category_enrichment = any(p.get('categories') for p in proposals_data[:5])
        
        assert has_github_enrichment, "GitHub enrichment not working"
        assert has_category_enrichment, "Category enrichment not working"
        
        print(f"✅ Proposals extraction successful: {len(proposals_data)} proposals found")

    @pytest.fixture(autouse=True)
    def cleanup_test_db(self):
        """Clean up test database after each test."""
        yield  # Run the test
        
        # Cleanup test databases
        test_files = ["lido_test.duckdb", "test_lido_pipeline.duckdb"]
        for file in test_files:
            if os.path.exists(file):
                os.remove(file)

    def test_full_pipeline(self):
        """Test complete dlt pipeline with small dataset."""
        # Create test pipeline
        pipeline = dlt.pipeline(
            pipeline_name="test_lido_pipeline",
            destination="duckdb",
            dataset_name="catalyst_test"
        )
        
        # Load funds
        funds_info = pipeline.run(funds(), table_name="funds")
        assert funds_info is not None, "Funds loading failed"
        
        # Load sample proposals
        proposals_info = pipeline.run(proposals_enriched(max_pages=1), table_name="proposals_sample")
        assert proposals_info is not None, "Proposals loading failed"
        
        # Verify data in database
        conn = duckdb.connect("test_lido_pipeline.duckdb")
        
        funds_count = conn.execute("SELECT COUNT(*) FROM catalyst_test.funds").fetchone()[0]
        proposals_count = conn.execute("SELECT COUNT(*) FROM catalyst_test.proposals_sample").fetchone()[0]
        
        conn.close()
        
        # Assertions
        assert funds_count > 0, "No funds found in database"
        assert proposals_count > 0, "No proposals found in database"
        
        print(f"✅ Pipeline test successful - Funds: {funds_count}, Proposals: {proposals_count}")


class TestLidoEnrichment:
    """Test suite for Lido data enrichment features."""

    def test_github_extraction(self):
        """Test GitHub link extraction functionality."""
        # Get a small sample to test enrichment
        proposals_data = list(proposals_enriched(max_pages=1))
        
        # Find proposals with GitHub links
        github_proposals = [p for p in proposals_data if p.get('has_github')]
        
        if github_proposals:
            sample = github_proposals[0]
            
            # Check GitHub enrichment structure
            assert 'github_links' in sample, "Missing github_links field"
            assert 'has_github' in sample, "Missing has_github field"
            assert sample['has_github'] is True, "has_github should be True for GitHub proposals"
            assert isinstance(sample['github_links'], list), "github_links should be a list"
            assert len(sample['github_links']) > 0, "github_links should not be empty"
            
            print(f"✅ GitHub extraction working: {len(github_proposals)} proposals with GitHub found")
        else:
            print("ℹ️  No GitHub proposals found in test sample")

    def test_category_classification(self):
        """Test category classification functionality."""
        # Get a small sample to test categorization
        proposals_data = list(proposals_enriched(max_pages=1))
        
        for proposal in proposals_data[:5]:  # Test first 5 proposals
            # Check category enrichment structure
            assert 'categories' in proposal, "Missing categories field"
            assert 'primary_category' in proposal, "Missing primary_category field"
            
            categories = proposal['categories']
            primary_category = proposal['primary_category']
            
            assert isinstance(categories, list), "categories should be a list"
            assert len(categories) > 0, "categories should not be empty"
            assert isinstance(primary_category, str), "primary_category should be a string"
            assert primary_category in categories, "primary_category should be in categories list"
            
        print("✅ Category classification working correctly")


class TestLidoIntegration:
    """Integration tests for Lido connector with real API calls."""

    @pytest.mark.slow
    def test_api_connectivity(self):
        """Test basic API connectivity (marked as slow test)."""
        # This test actually hits the API - mark as slow
        funds_data = list(funds())
        
        assert len(funds_data) >= 12, "Expected at least 12 Catalyst funds"
        
        # Check fund structure
        sample_fund = funds_data[0]
        assert sample_fund.get('id'), "Fund should have ID"
        assert sample_fund.get('title'), "Fund should have title"
        
        print(f"✅ API connectivity test passed: {len(funds_data)} funds retrieved")

    @pytest.mark.slow  
    def test_pagination_handling(self):
        """Test pagination handling (marked as slow test)."""
        # Test with limited pages to ensure pagination works
        proposals_page1 = list(proposals_enriched(max_pages=1))
        proposals_page2 = list(proposals_enriched(max_pages=2))
        
        assert len(proposals_page2) > len(proposals_page1), "Page 2 should have more proposals than page 1"
        assert len(proposals_page1) > 0, "Page 1 should have proposals"
        
        print(f"✅ Pagination test passed: Page 1 ({len(proposals_page1)}), Page 2 ({len(proposals_page2)})")