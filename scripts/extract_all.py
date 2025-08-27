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

def extract_github_data(sample: bool = True):
    """Extract GitHub data to tech_intel.duckdb"""
    print("🔍 Extracting GitHub data...")
    
    # Configure pipeline for single database
    pipeline = dlt.pipeline(
        pipeline_name='tech_intel',
        destination='duckdb',
        dataset_name='github_raw'
    )
    
    # Sample repositories for testing
    repos = ['cardano-foundation/cardano-wallet', 'input-output-hk/cardano-node']
    
    # Load repositories
    print("📁 Loading repositories...")
    pipeline.run(repositories(repos=repos), table_name='repositories')
    
    # Load pull requests (limit for sample)
    max_prs = 50 if sample else None
    print(f"🔀 Loading pull requests (max {max_prs or 'all'} per repo)...")
    pipeline.run(pull_requests(repos=repos, max_per_repo=max_prs), table_name='pull_requests')
    
    # Load releases (limit for sample)  
    max_releases = 10 if sample else None
    print(f"🏷️  Loading releases (max {max_releases or 'all'} per repo)...")
    pipeline.run(releases(repos=repos, max_per_repo=max_releases), table_name='releases')
    
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
    print("🚀 Starting unified data extraction...")
    print("=" * 50)
    
    # Extract both data sources
    extract_github_data(sample=True)
    extract_cardano_data(sample=True)
    
    print("=" * 50)
    print("🎯 Unified extraction completed!")
    print("📊 All data available in tech_intel.duckdb with schemas:")
    print("   - github_raw.repositories, github_raw.pull_requests, github_raw.releases")
    print("   - lido_raw.funds, lido_raw.proposals")

if __name__ == "__main__":
    main()