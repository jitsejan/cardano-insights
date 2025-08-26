"""GitHub API connector for Cardano ecosystem repository insights."""
from __future__ import annotations
from typing import Iterator, Dict, Any, Optional, List
import os
import requests
import dlt
from datetime import datetime


BASE_URL = "https://api.github.com"


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
def repositories(repos: Optional[List[str]] = None) -> Iterator[Dict[str, Any]]:
    """
    Fetch repository metadata for specified repositories.
    
    Args:
        repos: List of repository names in format "owner/repo"
    """
    if not repos:
        repos = [
            "cardano-foundation/cardano-wallet",
            "input-output-hk/cardano-node",
            "input-output-hk/plutus",
            "Emurgo/cardano-serialization-lib",
        ]
    
    for repo_name in repos:
        try:
            repo_data = _get_json(f"repos/{repo_name}")
            yield repo_data
        except Exception as e:
            print(f"Error fetching repository {repo_name}: {e}")
            continue


@dlt.resource(name="pull_requests", write_disposition="merge", primary_key="id")
def pull_requests(
    repos: Optional[List[str]] = None, 
    state: str = "all",
    max_per_repo: Optional[int] = None
) -> Iterator[Dict[str, Any]]:
    """
    Fetch pull requests for specified repositories.
    Raw GitHub API response - enrichment handled in dbt silver layer.
    
    Args:
        repos: List of repository names in format "owner/repo"
        state: PR state filter ("open", "closed", "all")
        max_per_repo: Maximum number of PRs per repository
    """
    if not repos:
        repos = [
            "cardano-foundation/cardano-wallet",
            "input-output-hk/cardano-node", 
            "input-output-hk/plutus",
            "Emurgo/cardano-serialization-lib",
        ]
    
    for repo_name in repos:
        print(f"Fetching pull requests for {repo_name}")
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
                
                prs = _get_json(f"repos/{repo_name}/pulls", params)
                
                if not prs:
                    print(f"No more PRs on page {page} for {repo_name}")
                    break
                
                print(f"Fetched {len(prs)} PRs from page {page} for {repo_name}")
                
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
    max_per_repo: Optional[int] = None
) -> Iterator[Dict[str, Any]]:
    """
    Fetch releases for specified repositories.
    Raw GitHub API response - enrichment handled in dbt silver layer.
    
    Args:
        repos: List of repository names in format "owner/repo"
        max_per_repo: Maximum number of releases per repository
    """
    if not repos:
        repos = [
            "cardano-foundation/cardano-wallet",
            "input-output-hk/cardano-node",
            "input-output-hk/plutus", 
            "Emurgo/cardano-serialization-lib",
        ]
    
    for repo_name in repos:
        print(f"Fetching releases for {repo_name}")
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