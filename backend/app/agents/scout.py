import asyncio
import os
from typing import List, Dict
from tavily import AsyncTavilyClient
from pydantic import BaseModel, Field

# 1. Structure the Signal A output for the Hunter
class RawEvent(BaseModel):
    company_name: str = Field(description="Extracted company name or 'TBD'")
    event_url: str = Field(description="Source URL of the signal")
    event_date: str = Field(description="When the event happened or was recorded")
    snippet: str = Field(description="Summary text of the event")
    source_type: str = Field(description="'Technical' (ArcGIS/Socrata) or 'General' (News/Web)")

class SignalScout:
    def __init__(self, tavily_key: str | None = None):
        resolved_key = tavily_key or os.getenv("tavily_search") or os.getenv("TAVILY_API_KEY")
        if not resolved_key:
            raise RuntimeError("Missing Tavily API key (set `tavily_search` in env).")
        self.client = AsyncTavilyClient(api_key=resolved_key)

    async def fetch_query(self, query: str) -> List[RawEvent]:
        """
        Executes a single search query with 'Advanced Depth' to find Signal A.
        """
        print(f"DEBUG: Scout searching: {query}")
        
        # search_depth="advanced" visits the page to ensure accuracy
        response = await self.client.search(
            query=query, 
            search_depth="advanced", 
            max_results=5
        )
        
        results = []
        for res in response['results']:
            # Auto-detect Technical vs General based on URL
            url = res['url'].lower()
            is_technical = any(x in url for x in ['.gov', 'arcgis', 'socrata', 'data.'])
            
            results.append(RawEvent(
                company_name="TBD", # Agent 3 (Hunter) will refine the official name
                event_url=res['url'],
                event_date=res.get('published_date', "Recent"),
                snippet=res['content'],
                source_type="Technical" if is_technical else "General"
            ))
        return results

    async def run(self, queries: List[str]) -> List[RawEvent]:
        """
        Runs all 3-5 queries IN PARALLEL for extreme speed.
        """
        # Start all searches at once
        tasks = [self.fetch_query(q) for q in queries]
        
        # Wait for all to finish simultaneously
        all_results = await asyncio.gather(*tasks)
        
        # Flatten the list of lists
        flattened = [event for sublist in all_results for event in sublist]
        
        print(f"DEBUG: Scout finished. Found {len(flattened)} potential Signal A events.")
        return flattened

# --- TEST EXECUTION ---
if __name__ == "__main__":
    # Example queries from the Concierge
    test_queries = [
        "New commercial building permits Austin 2024",
        "Recent office space lease signings Austin TX",
        "Austin new business grand openings October 2024"
    ]
    
    scout = SignalScout(tavily_key="your_tavily_api_key")
    
    # Run the async loop
    raw_events = asyncio.run(scout.run(test_queries))
    
    # This list now goes to Agent 3: The Technical Hunter
    for e in raw_events:
        print(f"[{e.source_type}] {e.event_url}")