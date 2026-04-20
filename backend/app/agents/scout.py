import os
import json
import httpx
import asyncio
from typing import Dict, List
from app.models.state import AgentState
import google.generativeai as genai

# Setup Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash-lite")

# World Standard RAG Rules for Technical Discovery
RAG_RULES = """
- Socrata: Use 'site:gov', 'resource', '.json', 'API'. Avoid 'dev.socrata.com/foundry'.
- ArcGIS: Use 'FeatureServer/0', 'MapServer/0', 'query?f=json'.
- Signal Hunting: Use 'topping out', 'groundbreaking', 'crane watch', 'issued permit'.
"""

async def call_serper(queries: List[str]) -> List[str]:
    """Execute multiple Serper searches in parallel to stay fast."""
    url = "https://google.serper.dev/search"
    headers = {
        'X-API-KEY': os.getenv("SERPER_API_KEY"),
        'Content-Type': 'application/json'
    }
    
    async with httpx.AsyncClient() as client:
        tasks = []
        for q in queries:
            tasks.append(client.post(url, headers=headers, json={"q": q, "num": 10}))
        
        responses = await asyncio.gather(*tasks)
        
        urls = []
        for resp in responses:
            if resp.status_code == 200:
                results = resp.json().get('organic', [])
                for r in results:
                    # Filter out low-signal documentation sites immediately
                    link = r.get('link', '')
                    if "dev.socrata.com" not in link and "documentation" not in link.lower():
                        urls.append(link)
        return list(set(urls)) # Deduplicate

async def scout_node(state: AgentState) -> Dict:
    """The Scout: Strategic Intent Router and URL Discovery."""
    user_query = state.get("user_query", "")
    retry_count = state.get("retry_count", 0)
    
    # CHECK: Is this an enrichment request from the Architect?
    # (If the Architect found a project but no address, we search for that specifically)
    enrichment_query = None
    if state.get("final_leads"):
        for lead in state["final_leads"]:
            if lead.status == "requires_enrichment":
                enrichment_query = lead.enrichment_query
                break

    if enrichment_query:
        print(f"🔍 Scout performing Targeted Enrichment: {enrichment_query}")
        target_urls = await call_serper([enrichment_query])
        return {"candidate_urls": target_urls}

    # STANDARD MODE: Industry Classification + Technical Query Expansion
    strategy_prompt = "BROAD SEARCH" if retry_count > 0 else "TECHNICAL API SEARCH"
    
    prompt = f"""
    You are a Strategic Lead Generation Scout.
    Strategy: {strategy_prompt}
    RAG Rules: {RAG_RULES}
    User Query: "{user_query}"
    
    1. CLASSIFY industry: 'construction_gov', 'retail_food', 'b2b_saas', or 'general'.
    2. GENERATE 5 high-signal queries.
       - If 'construction_gov': prioritize ArcGIS FeatureServers and SODA APIs.
       - If 'retail_food': prioritize Yelp, directories, and specialty roaster lists.
       - If 'b2b_saas': prioritize hiring boards and LinkedIn company pages.
    
    Return JSON: 
    {{
      "industry": "archetype",
      "search_queries": ["q1", "q2", "q3", "q4", "q5"]
    }}
    """

    response = model.generate_content(
        prompt, 
        generation_config={"response_mime_type": "application/json"}
    )
    
    scout_data = json.loads(response.text)
    print(f"🎯 Scout: Archetype [{scout_data['industry']}] | Strategy [{strategy_prompt}]")

    # Execute Parallel Search
    found_urls = await call_serper(scout_data["search_queries"])
    
    print(f"📡 Scout found {len(found_urls)} potential sources.")

    return {
        "industry": scout_data["industry"],
        "search_queries": scout_data["search_queries"],
        "candidate_urls": found_urls,
        "retry_count": retry_count
    }