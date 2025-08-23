from __future__ import annotations
from typing import Iterator, Dict, Any, Optional, List
import os, requests, dlt, re

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
    """All Catalyst funds (F1..current). NOTE: this endpoint returns a list."""
    data = _get_json("funds")
    # It’s a list, not {data: [...]}
    if isinstance(data, list):
        for f in data:
            yield f
    else:
        for f in data.get("data", []):
            yield f

@dlt.resource(name="proposals", write_disposition="merge", primary_key="id")
def proposals(fund_id: Optional[int] = None, max_pages: Optional[int] = None) -> Iterator[Dict[str, Any]]:
    """
    Catalyst proposals (paged). The API expects `fs[]` for fund filter,
    and uses `page` for page number and `per_page` for page size.
    Set max_pages to limit total pages fetched to prevent infinite loops.
    """
    page = 1
    total_yielded = 0
    
    while True:
        # Safety check: limit number of pages to prevent infinite loops
        if max_pages is not None and page > max_pages:
            print(f"Reached max_pages limit of {max_pages} - stopping. Total proposals: {total_yielded}")
            break
            
        params = {"page": page, "per_page": 50}   # correct API parameters, smaller page size
        if fund_id is not None:
            params["fs[]"] = fund_id            # <-- key change vs. fund_id=

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

        for p in rows:
            yield p
            total_yielded += 1
            
        print(f"Fetched page {page} with {len(rows)} proposals (total: {total_yielded})")

        # paginate if Laravel-style links are present; otherwise use size check
        next_url = payload.get("links", {}).get("next") if isinstance(payload, dict) else None
        if not next_url and len(rows) < params["per_page"]:
            print(f"No next page - stopping. Total proposals: {total_yielded}")
            break
        page += 1

def _extract_github_links(text: str) -> List[str]:
    """Extract GitHub links from text using regex."""
    if not text:
        return []
    
    github_pattern = r'https?://(?:www\.)?github\.com/[^\s\]\)\'"<>,]+'
    matches = re.findall(github_pattern, text, re.IGNORECASE)
    return list(set(matches))

def _categorize_proposal(title: str, problem: str, solution: str, experience: str) -> List[str]:
    """Derive categories from proposal content."""
    
    # Combine all text for analysis
    full_text = f"{title} {problem} {solution} {experience}".lower()
    
    categories = []
    
    # Define category keywords
    category_keywords = {
        "DeFi": ["defi", "dex", "swap", "lending", "borrowing", "yield", "liquidity", "amm", "trading", "finance", "stablecoin", "payment"],
        "NFT": ["nft", "non-fungible", "collectible", "artwork", "marketplace", "mint", "royalties", "metadata"],
        "Gaming": ["game", "gaming", "metaverse", "virtual", "play-to-earn", "p2e", "arcade", "mmorpg"],
        "Education": ["education", "learning", "university", "student", "course", "tutorial", "teaching", "academy", "bootcamp"],
        "Infrastructure": ["infrastructure", "node", "api", "sdk", "library", "framework", "protocol", "blockchain", "network"],
        "Developer Tools": ["developer", "development", "tools", "ide", "debugging", "testing", "deployment", "ci/cd", "devops"],
        "Governance": ["governance", "voting", "drep", "delegation", "proposal", "democracy", "decentralized", "dao"],
        "Privacy": ["privacy", "zero-knowledge", "zk", "anonymous", "confidential", "private", "encryption"],
        "Identity": ["identity", "did", "credential", "verification", "authentication", "kyc", "prism", "atala"],
        "IoT": ["iot", "internet of things", "sensor", "device", "hardware", "embedded", "monitoring"],
        "Social": ["social", "community", "networking", "chat", "communication", "forum", "media"],
        "Analytics": ["analytics", "data", "dashboard", "metrics", "monitoring", "insights", "reporting"],
        "Security": ["security", "audit", "vulnerability", "threat", "pentesting", "compliance", "safety"],
        "Wallet": ["wallet", "mobile", "desktop", "browser", "extension", "custody", "keys"],
        "Enterprise": ["enterprise", "business", "corporate", "b2b", "institutional", "commercial"],
        "Research": ["research", "academic", "science", "study", "analysis", "paper", "thesis"]
    }
    
    for category, keywords in category_keywords.items():
        if any(keyword in full_text for keyword in keywords):
            categories.append(category)
    
    # If no categories found, mark as "Other"
    if not categories:
        categories = ["Other"]
    
    return categories

@dlt.resource(name="proposals_enriched", write_disposition="merge", primary_key="id")
def proposals_enriched(fund_id: Optional[int] = None, max_pages: Optional[int] = None) -> Iterator[Dict[str, Any]]:
    """
    Enhanced proposals resource with GitHub links and categories.
    """
    page = 1
    total_yielded = 0
    
    while True:
        # Safety check: limit number of pages to prevent infinite loops
        if max_pages is not None and page > max_pages:
            print(f"Reached max_pages limit of {max_pages} - stopping. Total proposals: {total_yielded}")
            break
            
        params = {"page": page, "per_page": 50}   # correct API parameters
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

        for p in rows:
            # Extract GitHub links from all sources
            github_links = set()
            
            # Website field
            website = p.get('website')
            if website and 'github.com' in website.lower():
                github_links.add(website)
            
            # Embedded URIs
            embedded_uris = p.get('embedded_uris', [])
            if embedded_uris:
                for uri_group in embedded_uris:
                    if isinstance(uri_group, list):
                        for uri in uri_group:
                            if uri and 'github.com' in uri.lower():
                                github_links.add(uri)
            
            # Text fields
            text_fields = [p.get('problem', ''), p.get('solution', ''), p.get('experience', '')]
            for field in text_fields:
                github_links.update(_extract_github_links(field))
            
            # Add GitHub links to proposal
            if github_links:
                p['github_links'] = list(github_links)
                p['has_github'] = True
            else:
                p['github_links'] = []
                p['has_github'] = False
            
            # Categorize proposal
            categories = _categorize_proposal(
                p.get('title', ''),
                p.get('problem', ''),
                p.get('solution', ''),
                p.get('experience', '')
            )
            p['categories'] = categories
            p['primary_category'] = categories[0] if categories else "Other"
            
            yield p
            total_yielded += 1
            
        print(f"Fetched page {page} with {len(rows)} proposals (total: {total_yielded})")

        # paginate if Laravel-style links are present; otherwise use size check
        next_url = payload.get("links", {}).get("next") if isinstance(payload, dict) else None
        if not next_url and len(rows) < params["per_page"]:
            print(f"No next page - stopping. Total proposals: {total_yielded}")
            break
        page += 1

@dlt.resource(name="github_repositories", write_disposition="merge", primary_key="repo_full_name")
def github_repositories() -> Iterator[Dict[str, Any]]:
    """
    Extract unique GitHub repositories from proposals.
    This depends on proposals_enriched being run first.
    """
    # This would ideally read from the proposals_enriched table
    # For now, we'll collect repos as proposals are processed
    # This is a placeholder - in practice, this could be a post-processing step
    return iter([])  # Empty for now, will be filled by post-processing