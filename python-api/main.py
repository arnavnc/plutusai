from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
from typing import List, Dict
from openai import AsyncOpenAI, RateLimitError
from time import sleep
import json
import os

app = FastAPI(
    title="PlutusAI API",
    description="API for PlutusAI Research Funding Assistant",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# OpenAI and OpenAlex configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set")
print(f"API Key starts with: {OPENAI_API_KEY[:10]}...")  # Debug print - only show first few chars

client = AsyncOpenAI()  # Will automatically use OPENAI_API_KEY from environment
OPENALEX_API_URL = "https://api.openalex.org/works"

@app.get("/")
async def root():
    """Root endpoint to verify API is running"""
    return {
        "status": "online",
        "message": "PlutusAI API is running",
        "version": "1.0.0",
        "endpoints": [
            "/search",
            "/ask",
            "/generate_funding_report"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test OpenAI connection
        api_key_status = "valid" if OPENAI_API_KEY else "missing"
        return {
            "status": "healthy",
            "openai_api_key": api_key_status,
            "key_starts_with": OPENAI_API_KEY[:10] if OPENAI_API_KEY else None
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

class ProjectDescription(BaseModel):
    description: str
    max_results: int = 50  # Allow customizing result size

class FundingData(BaseModel):
    funder_name: str
    funder_id: str
    award_id: str | None
    award_amount: float | None
    paper_title: str
    paper_doi: str

@app.post("/generate_funding_report")
async def generate_funding_report(project: ProjectDescription):
    try:
        search_terms = await extract_search_terms(project.description)
        funders_data = await search_openalex_for_grants(search_terms, project.max_results)
        
        summary = await generate_summary(project.description, funders_data)
        
        result = {
            "search_terms": search_terms,
            "funders_data": funders_data,
            "summary": summary
        }
        
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def extract_search_terms(description: str) -> List[str]:
    """Uses OpenAI to extract relevant search terms with better prompt."""
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": """Extract 5-10 highly relevant search terms for academic research funding.
                Focus on specific technical terms and methodologies that funding agencies typically look for."""},
                {"role": "user", "content": description}
            ]
        )
        return [term.strip() for term in response.choices[0].message.content.split(",")]
    except RateLimitError:
        sleep(1)  # Basic rate limit handling
        return await extract_search_terms(description)

async def search_openalex_for_grants(search_terms: List[str], max_results: int) -> List[Dict]:
    """Enhanced OpenAlex search with better filtering and rate limiting."""
    funders_data = []
    papers_found = 0
    
    for term in search_terms:
        if papers_found >= max_results:
            break
            
        page = 1
        while papers_found < max_results:
            params = {
                "search": term,
                "per_page": 50,
                "page": page,
                "filter": "has_grants:true",  # Only get papers with grants
                "sort": "cited_by_count:desc"  # Get influential papers first
            }
            
            try:
                response = requests.get(OPENALEX_API_URL, params=params)
                response.raise_for_status()
                works = response.json().get("results", [])
                
                if not works:
                    break
                    
                for work in works:
                    if "grants" in work and work["grants"]:
                        funders_data.append({
                            "title": work.get("title"),
                            "grants": work.get("grants"),
                            "doi": work.get("doi"),
                            "cited_by_count": work.get("cited_by_count"),
                            "publication_year": work.get("publication_year")
                        })
                        papers_found += 1
                        
                        if papers_found >= max_results:
                            break
                
                page += 1
                sleep(0.1)  # Rate limiting
                
            except requests.exceptions.RequestException as e:
                print(f"Error fetching data for term {term}: {e}")
                break
                
    return funders_data

async def generate_summary(description: str, funders_data):
    """Uses OpenAI to summarize findings and recommend next steps."""
    prompt = f"""
    Project Description: {description}
    
    Funding Sources Identified:
    {funders_data}
    
    Provide an insightful summary on potential next steps for acquiring funding based on this data.
    """
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Summarize funding insights and provide next steps for grant acquisition."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
