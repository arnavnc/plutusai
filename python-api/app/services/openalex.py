from typing import List, Dict, Optional
import requests
from time import sleep
from ..config import settings
from ..models import Work, Funder
import asyncio

class OpenAlexService:
    def __init__(self):
        self.base_url = "https://api.openalex.org"
        self.headers = {"User-Agent": f"mailto:{settings.contact_email}"}

    async def search_for_grants(self, search_terms: List[str], max_results: int) -> List[Dict]:
        funders_data = []
        papers_found = 0
        
        print(f"Starting search with terms: {search_terms}")  # Debug log
        
        for term in search_terms:
            if papers_found >= max_results:
                break
                
            cursor = "*"
            while papers_found < max_results and cursor:
                params = {
                    "search": term.strip(),
                    "per_page": min(25, max_results - papers_found),
                    "cursor": cursor,
                    "filter": "has_grants:true"
                }
                
                try:
                    print(f"Making request for term: {term.strip()}")  # Debug log
                    response = requests.get(
                        f"{self.base_url}/works",
                        params=params,
                        headers=self.headers
                    )
                    response.raise_for_status()
                    data = response.json()
                    
                    print(f"Got response with {len(data.get('results', []))} results")  # Debug log
                    
                    if not data.get("results"):
                        print(f"No results found for term: {term}")  # Debug log
                        break
                        
                    for work in data["results"]:
                        if papers_found >= max_results:
                            return funders_data
                        
                        grants = work.get("grants", [])
                        if grants:  # Only process works that have grants
                            print(f"Found work with {len(grants)} grants: {work.get('title', '')}")  # Debug log
                            funders_data.append({
                                "id": work.get("id"),
                                "doi": work.get("doi"),
                                "title": work.get("title"),
                                "publication_year": work.get("publication_year"),
                                "grants": grants,
                                "cited_by_count": work.get("cited_by_count", 0)
                            })
                            papers_found += 1
                    
                    cursor = data.get("meta", {}).get("next_cursor")
                    print(f"Next cursor: {cursor}")  # Debug log
                    await asyncio.sleep(0.1)  # Rate limiting
                    
                except Exception as e:
                    print(f"Error fetching data for term {term}: {e}")
                    print(f"Full error details: {str(e)}")  # More detailed error logging
                    break
                    
        print(f"Search complete. Found {len(funders_data)} papers with grants")  # Debug log
        return funders_data

    async def get_funder_details(self, funder_id: str) -> Optional[Funder]:
        """Fetch detailed information about a specific funder."""
        try:
            response = requests.get(
                f"{self.base_url}/funders/{funder_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return Funder(**response.json())
        except requests.exceptions.RequestException:
            return None

    async def enrich_funders_data(self, funders_data: List[Dict]) -> List[Dict]:
        """Enrich funders data with additional information from OpenAlex."""
        unique_funder_ids = {
            grant["funder_id"] 
            for work in funders_data 
            for grant in work.get("grants", [])
            if grant.get("funder_id")
        }
        
        funder_details = {}
        for funder_id in unique_funder_ids:
            details = await self.get_funder_details(funder_id)
            if details:
                funder_details[funder_id] = details.dict()
        
        # Enrich the original data with funder details
        for work in funders_data:
            for grant in work.get("grants", []):
                if grant.get("funder_id") in funder_details:
                    grant["funder_details"] = funder_details[grant["funder_id"]]
        
        return funders_data

openalex_service = OpenAlexService() 