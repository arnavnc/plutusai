from typing import List
from openai import AsyncOpenAI
from time import sleep
from ..config import settings
import httpx

class OpenAIService:
    def __init__(self):
        # Create a custom httpx client without proxies
        http_client = httpx.AsyncClient(
            timeout=60.0,
            follow_redirects=True
        )
        
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            http_client=http_client
        )

    async def extract_search_terms(self, description: str) -> List[str]:
        """Uses OpenAI to extract relevant search terms with better prompt."""
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": """Extract 5-10 highly relevant search terms for academic research funding.
                    Focus on specific technical terms and methodologies that funding agencies typically look for.
                    Return only the terms without numbers or newlines, separated by commas."""},
                    {"role": "user", "content": description}
                ]
            )
            # Clean up the response - remove numbers, newlines, and extra whitespace
            terms = response.choices[0].message.content
            terms = [term.strip().lstrip('0123456789. ') for term in terms.split(',')]
            return [term for term in terms if term]  # Remove any empty terms
        except Exception as e:
            sleep(1)  # Basic rate limit handling
            return await self.extract_search_terms(description)

    async def format_funders_data_for_summary(self, funders_data: list) -> str:
        """Format funders data into a clear, structured text format for the AI."""
        formatted_text = []
        
        # Group by funder for better analysis
        funder_groups = {}
        for work in funders_data:
            for grant in work.get("grants", []):
                funder_name = grant.get("funder_display_name", "Unknown Funder")
                if funder_name not in funder_groups:
                    funder_groups[funder_name] = {
                        "papers": [],
                        "total_citations": 0,
                        "grant_count": 0,
                        "award_ids": set()  # Track unique award IDs
                    }
                
                funder_groups[funder_name]["papers"].append({
                    "title": work["title"],
                    "year": work["publication_year"],
                    "citations": work["cited_by_count"],
                    "award_id": grant.get("award_id")
                })
                if grant.get("award_id"):
                    funder_groups[funder_name]["award_ids"].add(grant["award_id"])
                funder_groups[funder_name]["total_citations"] += work["cited_by_count"]
                funder_groups[funder_name]["grant_count"] += 1

        # Format the grouped data
        formatted_text.append("Funding Organizations Analysis:")
        for funder, data in sorted(funder_groups.items(), key=lambda x: x[1]["total_citations"], reverse=True):
            formatted_text.append(f"\n{funder}")
            formatted_text.append(f"- Total Grants: {data['grant_count']}")
            formatted_text.append(f"- Total Citations: {data['total_citations']}")
            formatted_text.append(f"- Unique Award IDs: {len(data['award_ids'])}")
            formatted_text.append("- Recent Funded Papers:")
            
            # Sort papers by year (most recent first) and citations
            sorted_papers = sorted(
                data["papers"], 
                key=lambda x: (x["year"], x["citations"]), 
                reverse=True
            )[:3]  # Show only top 3 most recent/cited papers
            
            for paper in sorted_papers:
                paper_text = f"  * {paper['title']} ({paper['year']}, {paper['citations']} citations)"
                if paper["award_id"]:
                    paper_text += f" - Grant ID: {paper['award_id']}"
                formatted_text.append(paper_text)
        
        return "\n".join(formatted_text)

    async def generate_summary(self, description: str, funders_data: list) -> str:
        """Uses OpenAI to summarize findings and recommend next steps."""
        formatted_data = await self.format_funders_data_for_summary(funders_data)
        
        prompt = f"""
        Project Description: {description}
        
        Funding Data Analysis:
        {formatted_data}
        
        Please provide a structured analysis in the following format:

        1. Top Funding Organizations Most Relevant to This Project
        - [Organization Name]: [Brief description of relevance and funding history]
        (List 3-5 most relevant organizations)

        2. Typical Grant Sizes or Patterns
        - [Grant type/organization]: [Size range and key characteristics]
        (List 2-4 typical patterns)

        3. Specific Recommendations for Approaching These Funders
        - [Clear, actionable recommendation]
        (List 4-6 specific recommendations)

        4. Strategic Next Steps for Grant Applications
        - [Specific action item]
        (List 3-4 next steps)

        Focus on actionable insights and concrete next steps. Be specific about grant sizes and requirements when that information is available.
        """
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a research funding expert. Analyze funding patterns and provide strategic advice for grant acquisition. Be specific and actionable in your recommendations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,  # Lowered temperature for more consistent, structured output
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error generating summary: {e}")
            raise

openai_service = OpenAIService() 