import asyncio
import os
from typing import Dict, Optional, Type
from pydantic import BaseModel, Field
from firecrawl import FirecrawlApp

# 1. Define WHAT we want to find on EVERY site (The Universal Schema)
class ExtractedLeadInfo(BaseModel):
    company_name: str = Field(description="Official name of the business")
    owner_name: Optional[str] = Field(description="Name of the person in charge or point of contact")
    physical_address: str = Field(description="The address mentioned in the permit or news")
    event_details: str = Field(description="Briefly, what is happening? (e.g. New HVAC install)")
    website_url: Optional[str] = Field(description="The business website if found")
    phone_number: Optional[str] = Field(description="Contact number if listed")

class UniversalHunter:
    def __init__(self, api_key: Optional[str] = None):
        resolved_key = api_key or os.getenv("FIRECRAWL_API_KEY")
        if not resolved_key:
            raise RuntimeError("Missing FIRECRAWL_API_KEY")
        self.app = FirecrawlApp(api_key=resolved_key)

    async def run(self, url: str) -> Dict:
        """
        UNIVERSAL EXTRACTOR: Works for ArcGIS, Socrata, and Standard Web.
        """
        print(f"DEBUG: Universal Hunter visiting -> {url}")
        
        # Firecrawl 'Extract' handles the JS, Proxies, and AI Parsing in one call.
        # This is 10x more universal than manual scraping.
        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(
                None, 
                lambda: self.app.scrape_url(
                    url, 
                    params={
                        'formats': ['extract'], 
                        'extract': {'schema': ExtractedLeadInfo.model_json_schema()}
                    }
                )
            )
            
            # If Firecrawl finds the JSON, it returns it perfectly mapped to our Schema
            return {
                "status": "success",
                "data": result.get('extract', {}),
                "metadata": result.get('metadata', {})
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

# --- COMPACT EXECUTION ---
if __name__ == "__main__":
    hunter = UniversalHunter(api_key="fc-your-key")
    
    # This works for a Government Portal OR a regular news site
    test_url = "https://data.austintexas.gov/resource/8p39-m8p5"
    
    lead_data = asyncio.run(hunter.run(test_url))
    print(lead_data)