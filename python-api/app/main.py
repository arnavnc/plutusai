from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .models import ProjectDescription
from .services.cache import cache_service
from .services.openai_service import openai_service
from .services.openalex import openalex_service

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/generate_funding_report")
async def generate_funding_report(project: ProjectDescription):
    try:
        # Check cache first
        cache_key = f"funding_report:{hash(project.description)}"
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            return cached_result

        # Generate new report
        search_terms = await openai_service.extract_search_terms(project.description)
        funders_data = await openalex_service.search_for_grants(search_terms, project.max_results)
        
        # Enrich with additional funder information
        enriched_data = await openalex_service.enrich_funders_data(funders_data)
        
        summary = await openai_service.generate_summary(project.description, enriched_data)
        
        result = {
            "search_terms": search_terms,
            "funders_data": enriched_data,
            "summary": summary
        }
        
        # Cache the result
        await cache_service.set(cache_key, result)
        
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 