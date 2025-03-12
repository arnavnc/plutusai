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
        
        Provide a structured analysis following EXACTLY this format, maintaining the exact section headers:

        1. Top Funding Organizations Most Relevant to This Project
        [List 3-5 most relevant organizations with brief descriptions]
        - Each organization should be described in 2-3 sentences
        - Focus on their relevance to the project and funding history
        - Include specific details about their funding interests

        2. Typical Grant Sizes or Patterns
        [List 2-4 typical patterns]
        - Include specific dollar/currency amounts when available
        - Mention typical duration and funding cycles
        - Note any special requirements or preferences

        3. Specific Recommendations for Approaching These Funders
        [List 4-6 specific recommendations]
        - Each recommendation should be actionable and specific
        - Include timing considerations
        - Focus on concrete steps rather than general advice

        4. Strategic Next Steps for Grant Applications
        [List 3-4 next steps]
        - Each step should be immediately actionable
        - Include specific timeframes when possible
        - Focus on preparation and positioning

        Important:
        - Keep sections clearly separated
        - Use bullet points consistently
        - Be specific and quantitative where possible
        - Focus on actionable insights
        - Avoid repeating information between sections
        """
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a research funding expert. Provide clear, structured, and non-repetitive advice for grant acquisition. Focus on specific, actionable recommendations and clear organization of information."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Lower temperature for more structured output
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error generating summary: {e}")
            raise

    async def answer_question(self, question: str, search_description: str, funders_data: list, enriched_data: list, conversation_history: list = None, paper_details: dict = None) -> str:
        """Uses OpenAI to answer questions about the search results and specific papers."""
        formatted_data = await self.format_funders_data_for_summary(funders_data)
        
        # Format paper details for the prompt
        papers_context = ""
        if paper_details:
            papers_context = "\nDetailed Paper Information:\n"
            for title, paper in paper_details.items():
                papers_context += f"\nTitle: {paper['title']}"
                papers_context += f"\nYear: {paper['year']}"
                papers_context += f"\nCitations: {paper['citations']}"
                if paper['abstract']:
                    papers_context += f"\nAbstract: {paper['abstract']}"
                papers_context += "\nFunders:"
                for funder in paper['funders']:
                    papers_context += f"\n- {funder['name']}"
                    if funder['grant_id']:
                        papers_context += f" (Grant ID: {funder['grant_id']})"
                papers_context += "\n"
        
        # Build conversation context
        conversation_context = ""
        if conversation_history and len(conversation_history) > 2:  # Include context if there's more than the current exchange
            conversation_context = "\nPrevious Conversation:\n"
            # Include last 3 exchanges (6 messages) before the current one
            for msg in conversation_history[-7:-2]:  # Exclude current exchange
                role = "User" if msg["role"] == "user" else "Assistant"
                conversation_context += f"\n{role}: {msg['content']}\n"
        
        prompt = f"""
        Original Project Description: {search_description}
        
        User Question: {question}
        
        Funding Data Analysis:
        {formatted_data}{papers_context}{conversation_context}
        
        Please provide a detailed answer to the user's question based on the available data.
        If the question is about a specific paper, focus on that paper's details and its funding information.
        If it's a follow-up question, consider the context from previous exchanges.
        
        Guidelines for your response:
        - Be direct and specific in addressing the question
        - Use concrete examples from the funding data and paper details
        - Include relevant numbers, amounts, or statistics when available
        - Structure your response in a clear, easy-to-read format
        - If the question is about a specific paper:
          * Provide detailed information about that paper's funding sources
          * Explain the significance of the research
          * Highlight any unique aspects of the funding arrangement
        - If it's a follow-up question:
          * Maintain consistency with previous answers
          * Build upon previously provided information
          * Clarify any points from previous exchanges if needed
        - If the question cannot be fully answered with the available data, acknowledge this and provide the best possible answer
        - Keep your response focused and concise while being comprehensive
        
        Important:
        - Only make claims that are supported by the data provided
        - Use bullet points or sections if it helps organize the information
        - Highlight key insights or recommendations
        - If suggesting next steps, make them specific and actionable
        """
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a research funding expert specializing in analyzing grant opportunities and providing strategic advice. Your responses should be clear, specific, and grounded in the data provided. You can discuss specific papers in detail and maintain context across a conversation."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Lower temperature for more focused responses
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error answering question: {e}")
            raise

openai_service = OpenAIService() 