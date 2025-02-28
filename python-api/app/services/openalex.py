from typing import List, Dict, Optional
import requests
from time import sleep
from ..config import settings
from ..models import Work, Funder
import httpx
import asyncio

class OpenAlexService:
    def __init__(self):
        self.base_url = "https://api.openalex.org"
        self.headers = {"User-Agent": f"mailto:{settings.contact_email}"}

    async def search_for_grants(self, search_terms: List[str], max_results: int) -> List[Dict]:
        funders_data = []
        papers_found = 0
        
        print(f"Starting search with terms: {search_terms}")  # Debug log
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for term in search_terms:
                if papers_found >= max_results:
                    break
                    
                cursor = "*"
                papers_for_term = 0
                max_empty_pages = 3
                empty_page_count = 0
                
                while papers_found < max_results and cursor and empty_page_count < max_empty_pages:
                    params = {
                        "search": term.strip(),
                        "per_page": 50,  # Increased since we need to filter post-request
                        "cursor": cursor
                    }
                    
                    try:
                        response = await client.get(
                            f"{self.base_url}/works",
                            params=params,
                            headers=self.headers
                        )
                        response.raise_for_status()
                        data = response.json()
                        
                        results = data.get("results", [])
                        print(f"Got response with {len(results)} results")  # Debug log
                        
                        if not results:
                            empty_page_count += 1
                            break
                            
                        papers_with_grants = 0
                        for work in results:
                            grants = work.get("grants", [])
                            if grants and len(grants) > 0:  # Check if grants array exists and is not empty
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
                                papers_for_term += 1
                                papers_with_grants += 1
                                
                                if papers_found >= max_results:
                                    break
                        
                        if papers_with_grants == 0:
                            empty_page_count += 1
                        else:
                            empty_page_count = 0  # Reset counter if we found papers with grants
                        
                        cursor = data.get("meta", {}).get("next_cursor")
                        print(f"Next cursor: {cursor}")  # Debug log
                        await asyncio.sleep(0.1)  # Rate limiting
                        
                    except Exception as e:
                        print(f"Error fetching data for term {term}: {e}")
                        break
                
                print(f"Found {papers_for_term} papers with grants for term: {term}")  # Debug log
                        
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