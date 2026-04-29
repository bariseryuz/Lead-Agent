import asyncio
from typing import Dict, Optional
from pydantic import BaseModel, Field
# from supabase import create_client, Client # Optional: for Supabase integration

# 1. The Final Lead Package (The "Shiiman Lead Card")
class FinalLeadProfile(BaseModel):
    company_name: str
    contact_name: str
    contact_email: str
    linkedin_url: Optional[str]
    location: str
    
    # The "Intelligence" section
    signal_type: str
    pace_rating: str  # FAST, STEADY
    reasoning_pitch: str = Field(description="The 'Why Now' story for the user")
    
    # The "Trust" section
    accuracy_score: float
    verification_summary: str

class LeadBuilder:
    def __init__(self, db_url: Optional[str] = None, db_key: Optional[str] = None):
        # Initialize your database connection here (e.g., Supabase or PostgreSQL)
        # self.supabase: Client = create_client(db_url, db_key) if db_url else None
        pass

    def compose_narrative(self, signal_logic: Dict, verified_data: Dict) -> str:
        """
        Combines the Signal Logic with the Verified Truth to create a 
        human-readable 'Reasoning Pitch'.
        """
        # This creates the 'Signal B' story
        narrative = (
            f"I found a high-intent lead at {verified_data.get('company_name')}. "
            f"The trigger is a {signal_logic.get('event_summary')}. "
            f"Since they are {signal_logic.get('hidden_need')}, {verified_data.get('owner_name')} "
            f"is the best person to contact regarding your services."
        )
        return narrative

    async def save_to_shiiman_db(self, lead: FinalLeadProfile):
        """
        Saves the final lead to your database for the 'Save Lead' feature.
        """
        print(f"DEBUG: Saving Lead for {lead.company_name} to Database...")
        # Logic to insert into Supabase/PostgreSQL
        # await self.supabase.table("leads").insert(lead.dict()).execute()
        await asyncio.sleep(0.5) # Simulating DB Latency
        return True

    async def run(self, signal_plan: Dict, verified_info: Dict) -> FinalLeadProfile:
        """
        Final Step: Combines everything and packages it.
        """
        print("DEBUG: Building Final Lead Card...")
        
        narrative = self.compose_narrative(signal_plan, verified_info)
        
        final_lead = FinalLeadProfile(
            company_name=verified_info.get('company_name'),
            contact_name=verified_info.get('owner_name'),
            contact_email=verified_info.get('email', "Not Verified"),
            linkedin_url=verified_info.get('linkedin_url'),
            location=verified_info.get('physical_address', "Unknown"),
            signal_type=signal_plan.get('velocity'),
            pace_rating=signal_plan.get('velocity'),
            reasoning_pitch=narrative,
            accuracy_score=verified_info.get('confidence_score', 0.0),
            verification_summary=f"Email: {verified_info.get('email_status')}, LinkedIn: Found"
        )
        
        # Save to the database
        await self.save_to_shiiman_db(final_lead)
        
        return final_lead

# --- FINAL FLOW TEST ---
async def test_full_packaging():
    builder = LeadBuilder()
    
    # Data from Signal.py
    signal_plan = {
        "event_summary": "New Commercial Permit",
        "hidden_need": "installing new office infrastructure",
        "velocity": "FAST"
    }
    
    # Data from Verifier.py
    verified_info = {
        "company_name": "Google Austin",
        "owner_name": "Jane Doe",
        "email": "jane@google.com",
        "linkedin_url": "https://linkedin.com/in/janedoe",
        "physical_address": "Austin, TX",
        "email_status": "valid",
        "confidence_score": 0.99
    }
    
    final_card = await builder.run(signal_plan, verified_info)
    print("\n--- SHIIMAN LEAD CARD READY ---")
    print(final_card.json(indent=2))

if __name__ == "__main__":
    asyncio.run(test_full_packaging())