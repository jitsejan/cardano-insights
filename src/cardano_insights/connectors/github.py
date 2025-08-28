"""GitHub API connector for Cardano ecosystem repository insights."""
from __future__ import annotations
from typing import Iterator, Dict, Any, Optional, List
import os
import requests
import dlt
from datetime import datetime, timedelta
import duckdb
from pathlib import Path


BASE_URL = "https://api.github.com"
FRESHNESS_WINDOW_DAYS = 7


def _get_database_path() -> str:
    """Get the path to the tech_intel database."""
    # Try common locations
    paths = [
        "tech_intel.duckdb",
        "../tech_intel.duckdb", 
        "../../tech_intel.duckdb"
    ]
    
    for path in paths:
        if Path(path).exists():
            return path
    
    # Default to tech_intel.duckdb in current directory
    return "tech_intel.duckdb"


def _check_data_freshness(table_name: str, repo_name: Optional[str] = None) -> tuple[bool, Optional[datetime]]:
    """
    Check if data in the database is fresh (within FRESHNESS_WINDOW_DAYS).
    
    Args:
        table_name: Name of the table to check (repositories, pull_requests, releases)
        repo_name: Optional repository name filter
        
    Returns:
        Tuple of (is_fresh, last_updated_timestamp)
    """
    try:
        db_path = _get_database_path()
        if not Path(db_path).exists():
            print(f"Database {db_path} does not exist - full refresh needed")
            return False, None
            
        conn = duckdb.connect(db_path, read_only=True)
        
        # Build query based on table and optional repo filter
        # Try fetched_at first, fall back to updated_at for older data
        timestamp_columns = ["fetched_at", "updated_at"]
        result = None
        
        for col in timestamp_columns:
            try:
                if repo_name:
                    if table_name == "repositories":
                        query = f"SELECT MAX({col}) FROM github_raw.{table_name} WHERE full_name = ?"
                        params = [repo_name]
                    else:
                        query = f"SELECT MAX({col}) FROM github_raw.{table_name} WHERE repository_full_name = ?"
                        params = [repo_name]
                else:
                    query = f"SELECT MAX({col}) FROM github_raw.{table_name}"
                    params = []
                    
                result = conn.execute(query, params).fetchone()
                if result and result[0]:
                    print(f"Using {col} for freshness check")
                    break
            except Exception as e:
                print(f"Column {col} not found, trying next...")
                continue
        conn.close()
        
        if not result or not result[0]:
            print(f"No data found in {table_name} - full refresh needed")
            return False, None
            
        timestamp_value = result[0]
        try:
            # Handle different timestamp formats - string or datetime object
            if isinstance(timestamp_value, datetime):
                last_updated = timestamp_value
            elif isinstance(timestamp_value, str):
                if timestamp_value.endswith('Z'):
                    last_updated = datetime.fromisoformat(timestamp_value.replace('Z', '+00:00'))
                else:
                    last_updated = datetime.fromisoformat(timestamp_value)
            else:
                print(f"Unknown timestamp format: {type(timestamp_value)}")
                return False, None
        except Exception as e:
            print(f"Could not parse timestamp {timestamp_value}: {e}")
            return False, None
            
        cutoff = datetime.now() - timedelta(days=FRESHNESS_WINDOW_DAYS)
        
        is_fresh = last_updated.replace(tzinfo=None) > cutoff
        print(f"Data freshness check for {table_name}: last_updated={last_updated}, is_fresh={is_fresh}")
        return is_fresh, last_updated
        
    except Exception as e:
        print(f"Error checking data freshness: {e}")
        return False, None


def _get_last_updated_timestamp(table_name: str, repo_name: str) -> Optional[str]:
    """Get the last updated_at timestamp for incremental fetching."""
    try:
        db_path = _get_database_path()
        if not Path(db_path).exists():
            return None
            
        conn = duckdb.connect(db_path, read_only=True)
        
        # Get the most recent updated_at timestamp for this repo
        if table_name == "repositories":
            query = "SELECT MAX(updated_at) FROM github_raw.repositories WHERE full_name = ?"
        else:
            query = f"SELECT MAX(updated_at) FROM github_raw.{table_name} WHERE repository_full_name = ?"
            
        result = conn.execute(query, [repo_name]).fetchone()
        conn.close()
        
        if result and result[0]:
            return result[0]
        return None
        
    except Exception as e:
        print(f"Error getting last updated timestamp: {e}")
        return None


def _get_json(path: str, params: dict | None = None) -> dict | list:
    """Make authenticated GitHub API request."""
    url = f"{BASE_URL}/{path.lstrip('/')}"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "cardano-insights/0.1"
    }
    
    # Add GitHub token if available
    github_token = os.getenv("GITHUB_TOKEN")
    if github_token:
        headers["Authorization"] = f"token {github_token}"
    
    r = requests.get(
        url,
        headers=headers,
        params=params or {},
        timeout=60,
    )
    
    print("GET", r.url, "status", r.status_code, "remaining", r.headers.get("X-RateLimit-Remaining"))
    r.raise_for_status()
    
    if not r.text.strip():
        return []
    return r.json()


@dlt.resource(name="repositories", write_disposition="merge", primary_key="id")
def repositories(
    repos: Optional[List[str]] = None, 
    force_refresh: bool = False
) -> Iterator[Dict[str, Any]]:
    """
    Fetch repository metadata for specified repositories with incremental loading.
    
    Args:
        repos: List of repository names in format "owner/repo"
        force_refresh: Force refresh even if data is fresh
    """
    if not repos:
        repos = [
            "cardano-foundation/cardano-wallet",
            "input-output-hk/cardano-node",
            "input-output-hk/plutus",
            "Emurgo/cardano-serialization-lib",
        ]
    
    for repo_name in repos:
        # Check if we need to refresh this repo's data
        if not force_refresh:
            is_fresh, last_updated = _check_data_freshness("repositories", repo_name)
            if is_fresh:
                print(f"Repository {repo_name} data is fresh, skipping...")
                continue
        
        try:
            print(f"Fetching repository metadata for {repo_name}")
            repo_data = _get_json(f"repos/{repo_name}")
            repo_data["fetched_at"] = datetime.utcnow().isoformat()
            yield repo_data
        except Exception as e:
            print(f"Error fetching repository {repo_name}: {e}")
            continue


@dlt.resource(name="pull_requests", write_disposition="merge", primary_key="id")
def pull_requests(
    repos: Optional[List[str]] = None, 
    state: str = "all",
    max_per_repo: Optional[int] = None,
    force_refresh: bool = False
) -> Iterator[Dict[str, Any]]:
    """
    Fetch pull requests for specified repositories with incremental loading.
    Raw GitHub API response - enrichment handled in dbt silver layer.
    
    Args:
        repos: List of repository names in format "owner/repo"
        state: PR state filter ("open", "closed", "all")
        max_per_repo: Maximum number of PRs per repository
        force_refresh: Force refresh even if data is fresh
    """
    if not repos:
        repos = [
            "cardano-foundation/cardano-wallet",
            "input-output-hk/cardano-node", 
            "input-output-hk/plutus",
            "Emurgo/cardano-serialization-lib",
        ]
    
    for repo_name in repos:
        # Check if we need to refresh this repo's PR data
        if not force_refresh:
            is_fresh, last_updated = _check_data_freshness("pull_requests", repo_name)
            if is_fresh:
                print(f"Pull requests for {repo_name} are fresh, skipping...")
                continue
        
        # Get last updated timestamp for incremental fetching
        last_updated_timestamp = None if force_refresh else _get_last_updated_timestamp("pull_requests", repo_name)
        
        print(f"Fetching pull requests for {repo_name}")
        if last_updated_timestamp:
            print(f"  Incremental fetch since: {last_updated_timestamp}")
        
        page = 1
        fetched_count = 0
        
        while True:
            if max_per_repo and fetched_count >= max_per_repo:
                print(f"Reached max limit of {max_per_repo} PRs for {repo_name}")
                break
                
            try:
                params = {
                    "state": state,
                    "page": page,
                    "per_page": 100,
                    "sort": "updated",
                    "direction": "desc"
                }
                
                # Add since parameter for incremental fetching
                if last_updated_timestamp:
                    params["since"] = last_updated_timestamp
                
                prs = _get_json(f"repos/{repo_name}/pulls", params)
                
                if not prs:
                    print(f"No more PRs on page {page} for {repo_name}")
                    break
                
                print(f"Fetched {len(prs)} PRs from page {page} for {repo_name}")
                
                # If we're doing incremental and see old data, stop
                if last_updated_timestamp and prs:
                    oldest_pr_updated = prs[-1].get("updated_at", "")
                    if oldest_pr_updated and oldest_pr_updated <= last_updated_timestamp:
                        print(f"Reached previously fetched data, stopping...")
                        break
                
                for pr in prs:
                    # Add repository info to each PR
                    pr["repository_full_name"] = repo_name
                    pr["fetched_at"] = datetime.utcnow().isoformat()
                    yield pr
                    fetched_count += 1
                    
                    if max_per_repo and fetched_count >= max_per_repo:
                        break
                
                page += 1
                
            except Exception as e:
                print(f"Error fetching PRs for {repo_name} page {page}: {e}")
                break


@dlt.resource(name="releases", write_disposition="merge", primary_key="id")
def releases(
    repos: Optional[List[str]] = None,
    max_per_repo: Optional[int] = None,
    force_refresh: bool = False
) -> Iterator[Dict[str, Any]]:
    """
    Fetch releases for specified repositories with incremental loading.
    Raw GitHub API response - enrichment handled in dbt silver layer.
    
    Args:
        repos: List of repository names in format "owner/repo"
        max_per_repo: Maximum number of releases per repository
        force_refresh: Force refresh even if data is fresh
    """
    if not repos:
        repos = [
            "cardano-foundation/cardano-wallet",
            "input-output-hk/cardano-node",
            "input-output-hk/plutus", 
            "Emurgo/cardano-serialization-lib",
        ]
    
    for repo_name in repos:
        # Check if we need to refresh this repo's releases data
        if not force_refresh:
            is_fresh, last_updated = _check_data_freshness("releases", repo_name)
            if is_fresh:
                print(f"Releases for {repo_name} are fresh, skipping...")
                continue
        
        # Get last updated timestamp for incremental fetching
        last_updated_timestamp = None if force_refresh else _get_last_updated_timestamp("releases", repo_name)
        
        print(f"Fetching releases for {repo_name}")
        if last_updated_timestamp:
            print(f"  Incremental fetch since: {last_updated_timestamp}")
            
        page = 1
        fetched_count = 0
        
        while True:
            if max_per_repo and fetched_count >= max_per_repo:
                print(f"Reached max limit of {max_per_repo} releases for {repo_name}")
                break
                
            try:
                params = {
                    "page": page,
                    "per_page": 100
                }
                
                releases_data = _get_json(f"repos/{repo_name}/releases", params)
                
                if not releases_data:
                    print(f"No more releases on page {page} for {repo_name}")
                    break
                
                print(f"Fetched {len(releases_data)} releases from page {page} for {repo_name}")
                
                # If we're doing incremental and see old data, stop
                if last_updated_timestamp and releases_data:
                    oldest_release_updated = releases_data[-1].get("published_at", "")
                    if oldest_release_updated and oldest_release_updated <= last_updated_timestamp:
                        print(f"Reached previously fetched releases, stopping...")
                        break
                
                for release in releases_data:
                    # Add repository info to each release
                    release["repository_full_name"] = repo_name
                    release["fetched_at"] = datetime.utcnow().isoformat()
                    yield release
                    fetched_count += 1
                    
                    if max_per_repo and fetched_count >= max_per_repo:
                        break
                
                page += 1
                
            except Exception as e:
                print(f"Error fetching releases for {repo_name} page {page}: {e}")
                break


@dlt.resource(name="issues", write_disposition="merge", primary_key="id") 
def issues(
    repos: Optional[List[str]] = None,
    state: str = "all",
    max_per_repo: Optional[int] = None
) -> Iterator[Dict[str, Any]]:
    """
    Fetch issues for specified repositories.
    Raw GitHub API response - enrichment handled in dbt silver layer.
    
    Args:
        repos: List of repository names in format "owner/repo"
        state: Issue state filter ("open", "closed", "all")
        max_per_repo: Maximum number of issues per repository
    """
    if not repos:
        repos = [
            "cardano-foundation/cardano-wallet",
            "input-output-hk/cardano-node",
            "input-output-hk/plutus",
            "Emurgo/cardano-serialization-lib",
        ]
    
    for repo_name in repos:
        print(f"Fetching issues for {repo_name}")
        page = 1
        fetched_count = 0
        
        while True:
            if max_per_repo and fetched_count >= max_per_repo:
                print(f"Reached max limit of {max_per_repo} issues for {repo_name}")
                break
                
            try:
                params = {
                    "state": state,
                    "page": page,
                    "per_page": 100,
                    "sort": "updated",
                    "direction": "desc"
                }
                
                issues_data = _get_json(f"repos/{repo_name}/issues", params)
                
                if not issues_data:
                    print(f"No more issues on page {page} for {repo_name}")
                    break
                
                print(f"Fetched {len(issues_data)} issues from page {page} for {repo_name}")
                
                for issue in issues_data:
                    # Filter out pull requests (GitHub includes PRs in issues endpoint)
                    if "pull_request" not in issue:
                        # Add repository info to each issue
                        issue["repository_full_name"] = repo_name
                        issue["fetched_at"] = datetime.utcnow().isoformat()
                        yield issue
                        fetched_count += 1
                        
                        if max_per_repo and fetched_count >= max_per_repo:
                            break
                
                page += 1
                
            except Exception as e:
                print(f"Error fetching issues for {repo_name} page {page}: {e}")
                break