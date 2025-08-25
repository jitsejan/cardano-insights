from __future__ import annotations
from typing import Iterator, Dict, Any, Optional
import os, requests, dlt

BASE = os.getenv("LIDO_BASE_URL", "https://www.lidonation.com/api/catalyst-explorer").rstrip("/")

def _get_json(path: str, params: dict | None = None) -> dict | list:
    url = f"{BASE}/{path.lstrip('/')}"
    r = requests.get(
        url,
        headers={"accept": "application/json", "user-agent": "cardano-insights/0.1"},
        params=params or {},
        timeout=60,
    )
    # helpful debug
    print("GET", r.url, "status", r.status_code, "len", r.headers.get("Content-Length"))
    r.raise_for_status()
    if not r.text.strip():
        return []
    return r.json()

@dlt.resource(name="funds", write_disposition="merge", primary_key="id")
def funds() -> Iterator[Dict[str, Any]]:
    """All Catalyst funds (F1..current). Raw API response."""
    data = _get_json("funds")
    # It's a list, not {data: [...]}
    if isinstance(data, list):
        for f in data:
            yield f
    else:
        for f in data.get("data", []):
            yield f

@dlt.resource(name="proposals", write_disposition="merge", primary_key="id")
def proposals(fund_id: Optional[int] = None, max_pages: Optional[int] = None) -> Iterator[Dict[str, Any]]:
    """
    Raw proposals from Catalyst API. No enrichment - just raw API data.
    Enrichment will be handled by dbt in the silver layer.
    """
    page = 1
    total_yielded = 0
    
    while True:
        # Safety check: limit number of pages to prevent infinite loops
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
            
        # Some responses are { data: [...], links: {...} }; others may already be lists.
        rows = payload.get("data", []) if isinstance(payload, dict) else payload
        if not rows:
            print(f"No data on page {page} - stopping. Total proposals: {total_yielded}")
            break

        print(f"Fetched page {page} with {len(rows)} proposals (total: {total_yielded + len(rows)})")
        
        for p in rows:
            # Just yield raw API response - no enrichment
            yield p
            total_yielded += 1

        # Check if there's a next page
        if isinstance(payload, dict) and payload.get("links", {}).get("next") is None:
            print(f"No next page - stopping. Total proposals: {total_yielded}")
            break
        page += 1