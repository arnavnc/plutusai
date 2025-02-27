from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
import json
import asyncio
import traceback

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

@app.get("/generate_funding_report")
async def generate_funding_report(description: str = Query(...)):
    async def event_generator():
        try:
            # Start search terms generation
            print("Starting search terms generation...")  # Debug log
            await asyncio.sleep(0.1)
            yield {
                "event": "status",
                "data": json.dumps({"stage": "searchTerms", "status": "started"})
            }
            
            try:
                search_terms = await openai_service.extract_search_terms(description)
                # Limit to top 3 search terms
                search_terms = search_terms[:3]
                print(f"Generated search terms: {search_terms}")  # Debug log
            except Exception as e:
                print(f"Error in extract_search_terms: {str(e)}")
                print(traceback.format_exc())
                raise

            yield {
                "event": "status",
                "data": json.dumps({
                    "stage": "searchTerms",
                    "status": "completed",
                    "data": search_terms
                })
            }

            # Search for papers for each term
            papers_found = 0
            funders_data = []
            
            for term in search_terms:
                print(f"Searching papers for term: {term}")  # Debug log
                try:
                    term_papers = await openalex_service.search_for_grants([term], 10)  # Reduced max_results for testing
                    funders_data.extend(term_papers)
                    papers_found += len(term_papers)
                    print(f"Found {len(term_papers)} papers for term: {term}")  # Debug log
                except Exception as e:
                    print(f"Error searching papers for term {term}: {str(e)}")
                    print(traceback.format_exc())
                    raise

                yield {
                    "event": "status",
                    "data": json.dumps({
                        "stage": "paperSearch",
                        "status": "completed",
                        "term": term,
                        "count": len(term_papers)
                    })
                }

            # Compile funding data
            print("Starting funding data compilation...")  # Debug log
            try:
                enriched_data = await openalex_service.enrich_funders_data(funders_data)
            except Exception as e:
                print(f"Error enriching funders data: {str(e)}")
                print(traceback.format_exc())
                raise

            yield {
                "event": "status",
                "data": json.dumps({
                    "stage": "fundingData",
                    "status": "completed"
                })
            }

            # Generate summary
            print("Generating summary...")  # Debug log
            try:
                summary = await openai_service.generate_summary(description, enriched_data)
            except Exception as e:
                print(f"Error generating summary: {str(e)}")
                print(traceback.format_exc())
                raise

            yield {
                "event": "status",
                "data": json.dumps({
                    "stage": "summary",
                    "status": "completed"
                })
            }
            
            # Send final results
            result = {
                "search_terms": search_terms,
                "funders_data": enriched_data,
                "summary": summary
            }
            
            print("Sending final results...")  # Debug log
            yield {
                "event": "result",
                "data": json.dumps(result)
            }

        except Exception as e:
            print(f"Error in event_generator: {str(e)}")
            print(traceback.format_exc())
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)})
            }

    return EventSourceResponse(event_generator())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 