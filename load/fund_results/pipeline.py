#!/usr/bin/env python3
"""
Official Catalyst Fund Results pipeline.
Downloads authoritative voting results from Google Sheets CSV exports.
"""
import dlt
import requests
import csv
from io import StringIO
from datetime import datetime
from typing import Iterator, Dict, Any


# Fund results mapping - convert Google Sheets URLs to CSV export URLs
FUND_RESULTS = {
    13: "https://docs.google.com/spreadsheets/d/1Jesjo5hoLvBJfWF4E6_516urm_lfvtSW0fhkZhCMUmQ/export?format=csv&gid=1185817058",
    12: "https://docs.google.com/spreadsheets/d/1Wq1XdPCJuiBDjDECSrpm7RvIfpNMEHitsbveqVaPWnk/export?format=csv&gid=837754658", 
    11: "https://docs.google.com/spreadsheets/d/18mDkdQn8fufBr7Ab9oSlV14UvBTMoUHeS43KAJiYPgQ/export?format=csv&gid=896673639",
    10: "https://docs.google.com/spreadsheets/d/1NxtUdvC-BRSh2kIczpV1rLuxJKkJfbxnRwxUsYJ9O8Y/export?format=csv&gid=885359704",
    9: "https://docs.google.com/spreadsheets/d/1MycQL-dkqf1xEW8xcr7vqcfHY6D7MHnG9ylDKNLSnAA/export?format=csv",
    8: "https://docs.google.com/spreadsheets/d/15ELXp81NfvXHgrerTbuIofZOXBsdjocN1YgBK0gPP3E/export?format=csv&gid=2111315347",
    7: "https://docs.google.com/spreadsheets/d/19_TEovS_Gemwvz2qlc6jGPizqAY8ZeDrzbH3DSeXyto/export?format=csv&gid=309291557",
    6: "https://docs.google.com/spreadsheets/d/1y-7U88FRvsEEzm98KbEswUGuy4q-eTeoFTV3EFrc6b4/export?format=csv&gid=1183771745",
    5: "https://docs.google.com/spreadsheets/d/156SdqPYOBkC5iQQeOOZc9yXSYoNHb-J-wJrem-xax78/export?format=csv&gid=1848314097",
    4: "https://docs.google.com/spreadsheets/d/13NC6SZ5MzQsYb-ufbuQHakxvLvPtZWv_02Aq17PFErI/export?format=csv&gid=1538672709",
    3: "https://docs.google.com/spreadsheets/d/1ibl-9qpLRQiFhJQfcvIeSdfJr9LjGpU6WqHce6VIUnE/export?format=csv&gid=1538672709",
    2: "https://docs.google.com/spreadsheets/d/1beHJPUoLvOoSmqN69NIxGmZSWEUJOeI4Lf2TwTfRRVs/export?format=csv&gid=1751929066",
    # Fund 1 is a PDF, needs different handling
}


@dlt.resource(name="fund_results", write_disposition="replace", primary_key=["fund_number", "proposal_id"])
def fund_results() -> Iterator[Dict[str, Any]]:
    """Fetch official fund voting results from Google Sheets."""
    
    for fund_number, csv_url in FUND_RESULTS.items():
        print(f"📊 Fetching Fund {fund_number} results...")
        
        try:
            response = requests.get(csv_url, timeout=30)
            response.raise_for_status()
            
            # Parse CSV
            csv_content = StringIO(response.text)
            reader = csv.DictReader(csv_content)
            
            row_count = 0
            for row in reader:
                # Standardize column names and add metadata
                standardized_row = {
                    "fund_number": fund_number,
                    "proposal_id": row.get("Proposal") or row.get("proposal") or f"F{fund_number}-{row_count}",
                    "project_name": row.get("Project Name") or row.get("name") or row.get("title", ""),
                    "requested_ada": _parse_ada_amount(row.get("Requested ADA") or row.get("requested_ada") or "0"),
                    "votes_cast": _parse_number(row.get("Votes Cast") or row.get("votes_cast") or "0"),
                    "yes_votes_ada": _parse_ada_amount(row.get("Total Yes Votes in ADA") or row.get("yes_votes") or "0"),
                    "approval_status": row.get("Approval") or row.get("approval") or "UNKNOWN",
                    "funding_status": row.get("Funding Status") or row.get("funding_status") or "UNKNOWN",
                    "extracted_at": datetime.utcnow().isoformat(),
                    "fund_name": f"Fund {fund_number}",
                    # Keep original row for debugging
                    "raw_data": dict(row)
                }
                
                yield standardized_row
                row_count += 1
            
            print(f"✅ Fund {fund_number}: {row_count} proposals")
            
        except Exception as e:
            print(f"❌ Error fetching Fund {fund_number}: {e}")


def _parse_ada_amount(value: str) -> int:
    """Parse ADA amount from string, handling commas and formatting."""
    if not value:
        return 0
    # Remove commas, currency symbols, whitespace
    cleaned = str(value).replace(",", "").replace("₳", "").replace("â³", "").replace("ADA", "").strip()
    try:
        return int(float(cleaned))
    except (ValueError, TypeError):
        return 0


def _parse_number(value: str) -> int:
    """Parse number from string."""
    if not value:
        return 0
    cleaned = str(value).replace(",", "").strip()
    try:
        return int(float(cleaned))
    except (ValueError, TypeError):
        return 0


def main():
    """Main pipeline execution."""
    import os
    
    print("🗳️ Starting Fund Results pipeline...")
    
    s3_bucket = os.getenv("S3_BUCKET", "tech-intelligence-datalake")
    s3_prefix = os.getenv("S3_PREFIX", "bronze/fund_results")
    
    # Create pipeline for S3 
    pipeline = dlt.pipeline(
        pipeline_name="fund_results",
        destination="filesystem", 
        dataset_name="raw"
    )
    
    bucket_url = f"s3://{s3_bucket}/{s3_prefix}"
    
    # Load fund results data to S3
    info = pipeline.run(fund_results(), table_name="fund_results", credentials={"bucket_url": bucket_url})
    print(f"✅ Pipeline completed: {info}")


if __name__ == "__main__":
    main()