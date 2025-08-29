#!/usr/bin/env python3
"""
Lido Catalyst data pipeline for Fargate execution.
Writes bronze Parquet to S3 using dlt filesystem destination.
"""
import dlt
from datetime import datetime
from typing import Iterator, Dict, Any, Optional

# Import settings (with fallback for different execution contexts)
try:
    from .settings import LidoSettings
except ImportError:
    # Fallback for tests or different execution contexts
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent))
    from settings import LidoSettings

# Import common utilities (with fallback for development)
try:
    from load.common.utils import setup_logging, emit_completion_event
except ImportError:
    # Fallback for local development
    def setup_logging(): pass
    def emit_completion_event(*args, **kwargs): pass

def _get_json(path: str, params: dict | None = None) -> dict | list:
    """Make authenticated API request to Lido Catalyst API."""
    import requests
    
    url = f"{LidoSettings.LIDO_BASE_URL}/{path.lstrip('/')}"
    r = requests.get(
        url,
        headers={"accept": "application/json", "user-agent": "lido-ingestion/1.0"},
        params=params or {},
        timeout=60,
    )
    print("GET", r.url, "status", r.status_code, "len", r.headers.get("Content-Length"))
    r.raise_for_status()
    
    if not r.text.strip():
        return []
    return r.json()


@dlt.resource(name="funds", write_disposition="merge", primary_key="id")
def funds() -> Iterator[Dict[str, Any]]:
    """All Catalyst funds (F1..current). Raw API response."""
    print("🏛️ Fetching Catalyst funds...")
    data = _get_json("funds")
    
    count = 0
    if isinstance(data, list):
        for f in data:
            f["ingested_at"] = datetime.utcnow().isoformat()
            yield f
            count += 1
    else:
        for f in data.get("data", []):
            f["ingested_at"] = datetime.utcnow().isoformat()
            yield f
            count += 1
    
    print(f"✅ Fetched {count} funds")


@dlt.resource(name="proposals", write_disposition="merge", primary_key="id")
def proposals(
    fund_id: Optional[int] = None, 
    max_pages: Optional[int] = None
) -> Iterator[Dict[str, Any]]:
    """
    Raw proposals from Catalyst API. No enrichment - just raw API data.
    Enrichment will be handled by dbt in the silver layer.
    """
    print("📋 Fetching Catalyst proposals...")
    if fund_id:
        print(f"   Filtering by fund_id: {fund_id}")
    if max_pages:
        print(f"   Limited to {max_pages} pages")
    
    page = 1
    total_yielded = 0
    
    while True:
        if max_pages is not None and page > max_pages:
            print(f"Reached max_pages limit of {max_pages} - stopping. Total proposals: {total_yielded}")
            break
            
        params = {"page": page, "per_page": 50}
        if fund_id is not None:
            params["fs[]"] = fund_id

        try:
            payload = _get_json("proposals", params)
        except Exception as e:
            print(f"Error fetching proposals page {page}: {e}")
            break
            
        rows = payload.get("data", []) if isinstance(payload, dict) else payload
        if not rows:
            print(f"No data on page {page} - stopping. Total proposals: {total_yielded}")
            break

        print(f"Fetched page {page} with {len(rows)} proposals (total: {total_yielded + len(rows)})")
        
        for p in rows:
            p["ingested_at"] = datetime.utcnow().isoformat()
            yield p
            total_yielded += 1

        if isinstance(payload, dict) and payload.get("links", {}).get("next") is None:
            print(f"No next page - stopping. Total proposals: {total_yielded}")
            break
        page += 1
    
    print(f"✅ Fetched {total_yielded} proposals")


def main():
    """Main pipeline execution - environment aware.""" 
    setup_logging()
    
    # Validate configuration
    LidoSettings.validate()
    
    environment = LidoSettings.ENVIRONMENT
    print(f"🚀 Starting Lido pipeline for environment: {environment}")
    
    if environment == "dev":
        print("📊 DEV MODE:")
        print("  📁 DuckDB: tech_intel.duckdb (for local analysis)")
        print(f"  ☁️  S3: s3://{LidoSettings.S3_BUCKET}/{LidoSettings.S3_PREFIX}/ (for cloud testing)")
        run_dev_pipeline()
    else:
        print("📊 PROD MODE:")
        print(f"  ☁️  S3: s3://{LidoSettings.S3_BUCKET}/{LidoSettings.S3_PREFIX}/")
        run_prod_pipeline()


def run_dev_pipeline():
    """Development pipeline - dual write to DuckDB + S3."""
    max_pages = LidoSettings.get_max_pages()
    
    # 1. Write to DuckDB for local analysis
    print("📁 Writing to local DuckDB for analysis...")
    local_pipeline = dlt.pipeline(
        pipeline_name="lido_local",
        destination="duckdb",
        dataset_name="lido_raw"
    )
    
    # Load all data to local DuckDB (always full dump for Lido)
    local_pipeline.run(funds(), table_name="funds")
    local_pipeline.run(proposals(max_pages=max_pages), table_name="proposals")
    
    # 2. Write to S3 for cloud testing
    print("☁️ Writing to S3 for cloud pipeline testing...")
    s3_pipeline = dlt.pipeline(
        pipeline_name="lido_s3_dev", 
        destination="filesystem",
        dataset_name="raw"
    )
    
    bucket_url = f"s3://{LidoSettings.S3_BUCKET}/{LidoSettings.S3_PREFIX}"
    s3_pipeline.run(funds(), table_name="funds", credentials={"bucket_url": bucket_url})
    s3_pipeline.run(proposals(max_pages=max_pages), table_name="proposals", credentials={"bucket_url": bucket_url})
    
    print("✅ DEV: Dual write completed (DuckDB + S3)")


def run_prod_pipeline():
    """Production pipeline - S3 only (Lido is always full dump)."""
    max_pages = LidoSettings.get_max_pages()  # None for prod = full dataset
    
    # Configure dlt for S3 filesystem destination
    pipeline = dlt.pipeline(
        pipeline_name="lido_catalyst",
        destination="filesystem", 
        dataset_name="raw"
    )
    
    bucket_url = f"s3://{LidoSettings.S3_BUCKET}/{LidoSettings.S3_PREFIX}"
    
    # Lido is always a full dump - no state tracking needed
    print("💰 Loading funds to S3 (full dump)...")
    pipeline.run(funds(), table_name="funds", credentials={"bucket_url": bucket_url})
    
    print(f"📋 Loading proposals to S3 (full dump, max_pages: {max_pages or 'all'})...")
    pipeline.run(proposals(max_pages=max_pages), table_name="proposals", credentials={"bucket_url": bucket_url})
    
    print("✅ PROD: S3 write completed")
    
    # Emit success event for downstream dbt processing
    emit_completion_event(
        source="techint.lido",
        detail_type="ingestion.complete",
        detail={
            "env": LidoSettings.ENVIRONMENT,
            "pipeline": "lido_catalyst",
            "timestamp": datetime.utcnow().isoformat(),
            "bucket": LidoSettings.S3_BUCKET,
            "prefix": LidoSettings.S3_PREFIX
        }
    )


if __name__ == "__main__":
    main()