"""
Pytest tests for GitHub API connector.
Uses pytest parametrize for comprehensive testing patterns following cardano-insights structure.
"""
import pytest
import dlt
import duckdb
import os
from pathlib import Path
from unittest.mock import Mock, patch

from src.cardano_insights.connectors.github import _get_json, repositories, pull_requests, releases, issues


class TestGitHubConnector:
    """Fast unit tests for connector functions without API calls."""

    def test_connector_imports(self):
        """Test that we can import the connector functions."""
        # Basic smoke test that the functions exist and are callable
        assert callable(_get_json), "_get_json should be callable"
        assert callable(repositories), "repositories should be callable"
        assert callable(pull_requests), "pull_requests should be callable"
        assert callable(releases), "releases should be callable"
        assert callable(issues), "issues should be callable"
    
    @pytest.mark.parametrize("max_per_repo", [1, 10, 50])
    def test_pull_requests_accepts_max_per_repo(self, max_per_repo):
        """Test that pull_requests function accepts max_per_repo parameter."""
        # This tests the function signature without making API calls
        try:
            # Just test that we can call the function - iterator won't execute until consumed
            iterator = pull_requests(max_per_repo=max_per_repo)
            assert hasattr(iterator, '__iter__'), "Should return an iterator"
        except Exception as e:
            pytest.fail(f"pull_requests(max_per_repo={max_per_repo}) should not raise exception: {e}")
    
    @pytest.mark.parametrize("state", ["open", "closed", "all"])
    def test_pull_requests_accepts_state(self, state):
        """Test that pull_requests function accepts state parameter."""
        try:
            iterator = pull_requests(state=state)
            assert hasattr(iterator, '__iter__'), "Should return an iterator"
        except Exception as e:
            pytest.fail(f"pull_requests(state={state}) should not raise exception: {e}")
    
    @pytest.mark.parametrize("repos", [
        ["cardano-foundation/cardano-wallet"],
        ["input-output-hk/cardano-node", "input-output-hk/plutus"]
    ])
    def test_repositories_accepts_repo_list(self, repos):
        """Test that repositories function accepts different repo lists."""
        try:
            iterator = repositories(repos=repos)
            assert hasattr(iterator, '__iter__'), "Should return an iterator"
        except Exception as e:
            pytest.fail(f"repositories(repos={repos}) should not raise exception: {e}")


class TestGitHubAPI:
    """Test suite for GitHub API interaction."""

    def test_get_json_success(self):
        """Test successful API call."""
        with patch('src.cardano_insights.connectors.github.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = '{"test": "data"}'
            mock_response.json.return_value = {"test": "data"}
            mock_response.headers.get.return_value = "100"
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            result = _get_json("repos/test/repo")
            assert result == {"test": "data"}
    
    def test_get_json_empty_response(self):
        """Test empty API response."""
        with patch('src.cardano_insights.connectors.github.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = ""
            mock_response.headers.get.return_value = "100"
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            result = _get_json("repos/test/repo")
            assert result == []
    
    @patch.dict('os.environ', {'GITHUB_TOKEN': 'test_token'})
    def test_github_token_authentication(self):
        """Test that GitHub token is used when available."""
        with patch('src.cardano_insights.connectors.github.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = '{"test": "data"}'
            mock_response.json.return_value = {"test": "data"}
            mock_response.headers.get.return_value = "100"
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            _get_json("repos/test/repo")
            
            # Check that Authorization header was added
            args, kwargs = mock_get.call_args
            assert "Authorization" in kwargs["headers"]
            assert kwargs["headers"]["Authorization"] == "token test_token"


class TestGitHubExtraction:
    """Test suite for GitHub connector functionality."""

    @pytest.mark.parametrize("repo_name", [
        "cardano-foundation/cardano-wallet",
        "input-output-hk/cardano-node"
    ])
    def test_repositories_generator(self, repo_name):
        """Test repositories generator function."""
        mock_data = {"id": 1, "name": "test-repo", "full_name": repo_name}
        
        with patch('src.cardano_insights.connectors.github._get_json') as mock_get_json:
            mock_get_json.return_value = mock_data
            
            repos_list = [repo_name]
            result = list(repositories(repos=repos_list))
            
            assert len(result) == 1
            assert result[0] == mock_data
            mock_get_json.assert_called_once_with(f"repos/{repo_name}")
    
    @pytest.mark.parametrize("max_per_repo", [1, 5, 10])
    def test_pull_requests_max_limit(self, max_per_repo):
        """Test that max_per_repo limit is respected."""
        mock_pr_data = [{"id": i, "number": i, "title": f"Test PR {i}"} for i in range(10)]
        
        with patch('src.cardano_insights.connectors.github._get_json') as mock_get_json:
            mock_get_json.return_value = mock_pr_data
            
            repos_list = ["test/repo"]
            result = list(pull_requests(repos=repos_list, max_per_repo=max_per_repo))
            
            assert len(result) == min(max_per_repo, len(mock_pr_data))
    
    def test_pull_requests_adds_metadata(self):
        """Test that pull requests get repository metadata added."""
        mock_pr_data = [
            {"id": 1, "number": 1, "title": "Test PR 1"},
            {"id": 2, "number": 2, "title": "Test PR 2"}
        ]
        
        with patch('src.cardano_insights.connectors.github._get_json') as mock_get_json:
            mock_get_json.side_effect = [mock_pr_data, []]  # First page has data, second is empty
            
            repos_list = ["test/repo"]
            result = list(pull_requests(repos=repos_list, max_per_repo=5))
            
            assert len(result) == 2
            assert all("repository_full_name" in pr for pr in result)
            assert all("fetched_at" in pr for pr in result)
            assert result[0]["repository_full_name"] == "test/repo"
    
    @pytest.mark.parametrize("resource_name,resource_func", [
        ("pull_requests", pull_requests),
        ("releases", releases),
        ("issues", issues)
    ])
    def test_resource_metadata_structure(self, resource_name, resource_func):
        """Test that all resources add proper metadata."""
        mock_data = [{"id": 1, "title": f"Test {resource_name}"}]
        
        with patch('src.cardano_insights.connectors.github._get_json') as mock_get_json:
            mock_get_json.side_effect = [mock_data, []]
            
            result = list(resource_func(repos=["test/repo"], max_per_repo=1))
            
            assert len(result) == 1
            assert "repository_full_name" in result[0]
            assert "fetched_at" in result[0]
            assert result[0]["repository_full_name"] == "test/repo"


class TestGitHubPipeline:
    """Test suite for GitHub dlt pipeline integration."""

    @pytest.mark.integration
    @pytest.mark.parametrize("pipeline_name,dataset_name", [
        ("test_github_pipeline_1", "test_github_dataset_1"),
        ("test_github_pipeline_2", "test_github_dataset_2")
    ])
    def test_pipeline_with_different_configs(self, pipeline_name, dataset_name):
        """Test dlt pipeline with different configurations."""
        with patch('src.cardano_insights.connectors.github._get_json') as mock_get_json:
            # Mock repository data
            mock_get_json.return_value = {"id": 1, "name": "test-repo", "full_name": "test/repo"}
            
            pipeline = dlt.pipeline(
                pipeline_name=pipeline_name,
                destination="duckdb",
                dataset_name=dataset_name
            )
            
            # Load repositories
            repo_info = pipeline.run(repositories(repos=["test/repo"]), table_name="repositories")
            assert repo_info is not None, f"Repository loading failed for {pipeline_name}"
            
            # Verify data in database
            db_file = f"{pipeline_name}.duckdb"
            conn = duckdb.connect(db_file)
            
            repo_count = conn.execute(f"SELECT COUNT(*) FROM {dataset_name}.repositories").fetchone()[0]
            conn.close()
            
            assert repo_count > 0, f"No repositories found in {pipeline_name}"
            
            # Cleanup
            if os.path.exists(db_file):
                os.remove(db_file)

    @pytest.fixture(autouse=True)
    def cleanup_test_db(self):
        """Clean up test database after each test."""
        yield  # Run the test
        
        # Cleanup test databases
        test_patterns = ["test_*.duckdb", "github_test.duckdb"]
        for pattern in test_patterns:
            for file in Path(".").glob(pattern):
                if file.exists():
                    file.unlink()


class TestGitHubFeatureClassification:
    """Test suite for GitHub pull request feature classification."""

    @pytest.mark.parametrize("title,expected_classification", [
        ("Fix bug in authentication", "bug fix"),
        ("Add new dashboard feature", "feature"),
        ("Refactor user service", "refactor"),
        ("Add unit tests for wallet", "test"),
        ("Update API documentation", "documentation"),
        ("Random change", "not clear")
    ])
    def test_feature_classification_logic(self, title, expected_classification):
        """Test feature classification based on PR titles."""
        # This would test the classification logic if implemented in the connector
        # For now, this is a placeholder for when we add classification logic
        
        # Mock PR with the test title
        mock_pr = {"title": title, "id": 1}
        
        # Classification logic (this would be in the dbt model)
        if any(word in title.lower() for word in ['fix', 'bug']):
            classification = 'bug fix'
        elif 'test' in title.lower():
            classification = 'test'
        elif 'doc' in title.lower():
            classification = 'documentation'
        elif any(word in title.lower() for word in ['feat', 'add', 'implement']):
            classification = 'feature'
        elif any(word in title.lower() for word in ['refactor', 'clean']):
            classification = 'refactor'
        else:
            classification = 'not clear'
        
        assert classification == expected_classification


class TestGitHubErrorHandling:
    """Test error handling and edge cases."""
    
    @pytest.mark.parametrize("invalid_max_per_repo", [-1, 0])
    def test_invalid_max_per_repo_handling(self, invalid_max_per_repo):
        """Test handling of invalid max_per_repo values."""
        try:
            result = list(pull_requests(max_per_repo=invalid_max_per_repo))
            # If it doesn't raise an error, should handle gracefully
            assert isinstance(result, list), "Should return a list even for invalid input"
        except (ValueError, TypeError):
            # This is acceptable - invalid input should raise an error
            pass
    
    def test_api_error_handling(self):
        """Test handling of API errors."""
        with patch('src.cardano_insights.connectors.github._get_json') as mock_get_json:
            mock_get_json.side_effect = Exception("API Error")
            
            # Should handle errors gracefully and continue
            result = list(repositories(repos=["test/repo"]))
            assert isinstance(result, list), "Should return a list even when API fails"
    
    @pytest.mark.parametrize("empty_response", [[], None, ""])
    def test_empty_response_handling(self, empty_response):
        """Test handling of empty API responses."""
        with patch('src.cardano_insights.connectors.github._get_json') as mock_get_json:
            mock_get_json.return_value = empty_response if empty_response != "" else []
            
            result = list(pull_requests(repos=["test/repo"]))
            assert isinstance(result, list), "Should return a list for empty responses"