#!/usr/bin/env python3
"""Simple script to check database status"""
import duckdb
import sys

try:
    conn = duckdb.connect('tech_intel.duckdb', read_only=True)
    
    # Check GitHub data
    try:
        github_repos = conn.execute('SELECT COUNT(*) FROM github_raw.repositories').fetchone()[0]
        github_prs = conn.execute('SELECT COUNT(*) FROM github_raw.pull_requests').fetchone()[0]
        github_releases = conn.execute('SELECT COUNT(*) FROM github_raw.releases').fetchone()[0]
        print(f'   📊 GitHub Data:')
        print(f'     - Repositories: {github_repos:,}')
        print(f'     - Pull Requests: {github_prs:,}')
        print(f'     - Releases: {github_releases:,}')
    except Exception:
        print('   📊 GitHub Data: Not loaded')
    
    # Check Catalyst data
    try:
        catalyst_funds = conn.execute('SELECT COUNT(*) FROM lido_raw.funds').fetchone()[0]
        catalyst_proposals = conn.execute('SELECT COUNT(*) FROM lido_raw.proposals').fetchone()[0]
        print(f'   🏛️  Catalyst Data:')
        print(f'     - Funds: {catalyst_funds:,}')
        print(f'     - Proposals: {catalyst_proposals:,}')
    except Exception:
        print('   🏛️  Catalyst Data: Not loaded')
    
    conn.close()
    
except Exception as e:
    print(f'   ❌ Error accessing database: {e}')
    sys.exit(1)