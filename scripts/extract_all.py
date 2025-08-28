#!/usr/bin/env python3
"""
Unified data extraction script for tech intelligence platform.
Extracts both GitHub and Cardano data into single tech_intel.duckdb database.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import dlt
from src.cardano_insights.connectors.github import repositories, pull_requests, releases
from src.cardano_insights.connectors.lido import funds, proposals

def extract_github_data(sample: bool = True, force_refresh: bool = False):
    """Extract GitHub data to tech_intel.duckdb with incremental loading"""
    print("🔍 Extracting GitHub data...")
    if force_refresh:
        print("⚡ Force refresh enabled - will fetch all data")
    else:
        print("📅 Using incremental loading - will skip fresh data")
    
    # Configure pipeline for single database
    pipeline = dlt.pipeline(
        pipeline_name='tech_intel',
        destination='duckdb',
        dataset_name='github_raw'
    )
    
    # Sample repositories for testing
    repos = ['cardano-foundation/cardano-wallet', 'input-output-hk/cardano-node']
    
    # Load repositories with incremental logic
    print("📁 Loading repositories...")
    pipeline.run(repositories(repos=repos, force_refresh=force_refresh), table_name='repositories')
    
    # Load pull requests (limit for sample)
    max_prs = 50 if sample else None
    print(f"🔀 Loading pull requests (max {max_prs or 'all'} per repo)...")
    pipeline.run(pull_requests(repos=repos, max_per_repo=max_prs, force_refresh=force_refresh), table_name='pull_requests')
    
    # Load releases (limit for sample)  
    max_releases = 10 if sample else None
    print(f"🏷️  Loading releases (max {max_releases or 'all'} per repo)...")
    pipeline.run(releases(repos=repos, max_per_repo=max_releases, force_refresh=force_refresh), table_name='releases')
    
    print("✅ GitHub data extraction completed")

def extract_cardano_data(sample: bool = True):
    """Extract Cardano/Catalyst data to tech_intel.duckdb"""
    print("🏛️  Extracting Cardano/Catalyst data...")
    
    # Configure pipeline for single database
    pipeline = dlt.pipeline(
        pipeline_name='tech_intel',
        destination='duckdb', 
        dataset_name='lido_raw'
    )
    
    # Load funds
    print("💰 Loading Catalyst funds...")
    pipeline.run(funds(), table_name='funds')
    
    # Load proposals (limit for sample)
    if sample:
        print("📋 Loading sample proposals (2 pages)...")
        pipeline.run(proposals(max_pages=2), table_name='proposals')
    else:
        print("📋 Loading ALL proposals (this will take time)...")
        pipeline.run(proposals(), table_name='proposals')
    
    print("✅ Cardano/Catalyst data extraction completed")

def main():
    """Extract all data to single tech_intel.duckdb"""
    import sys
    
    # Check for force refresh flag
    force_refresh = '--force' in sys.argv or '--force-refresh' in sys.argv
    
    print("🚀 Starting unified data extraction...")
    if force_refresh:
        print("⚡ Force refresh mode enabled")
    print("=" * 50)
    
    # Extract both data sources
    extract_github_data(sample=True, force_refresh=force_refresh)
    extract_cardano_data(sample=True)
    
    print("=" * 50)
    print("🎯 Unified extraction completed!")
    print("📊 All data available in tech_intel.duckdb with schemas:")
    print("   - github_raw.repositories, github_raw.pull_requests, github_raw.releases")
    print("   - lido_raw.funds, lido_raw.proposals")
    print()
    if not force_refresh:
        print("💡 Next time run with --force to refresh all data regardless of freshness")

if __name__ == "__main__":
    main()