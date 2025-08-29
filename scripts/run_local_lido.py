#!/usr/bin/env python3
"""
Local development runner for Lido pipeline.
Simulates Fargate execution but writes to local DuckDB for development.
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import dlt
from load.lido.pipeline import funds, proposals


def main():
    """Run Lido pipeline locally for development."""
    print("🚀 Running Lido pipeline locally...")
    print("📊 Target: Local DuckDB (lido_local.duckdb)")
    
    # Configure dlt for local DuckDB
    pipeline = dlt.pipeline(
        pipeline_name="lido_local",
        destination="duckdb",
        dataset_name="lido_raw"
    )
    
    try:
        # Check for sample mode
        sample_mode = "--sample" in sys.argv
        max_pages = 3 if sample_mode else None
        
        print("💰 Loading funds...")
        pipeline.run(funds(), table_name="funds")
        
        print(f"📋 Loading proposals ({'sample' if sample_mode else 'all'})...")
        pipeline.run(proposals(max_pages=max_pages), table_name="proposals")
        
        print("✅ Local Lido pipeline completed")
        
        # Show summary
        import duckdb
        conn = duckdb.connect("lido_local.duckdb")
        
        funds_count = conn.execute("SELECT COUNT(*) FROM lido_raw.funds").fetchone()[0]
        proposals_count = conn.execute("SELECT COUNT(*) FROM lido_raw.proposals").fetchone()[0]
        
        print(f"📊 Data loaded:")
        print(f"   - {funds_count} funds")
        print(f"   - {proposals_count} proposals")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Local pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()