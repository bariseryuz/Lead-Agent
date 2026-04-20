import asyncio
import os
from dotenv import load_dotenv

# 1. Load the environment variables from .env
load_dotenv()

# 2. Import the compiled graph (app) from your project structure
# Since graph.py is inside the 'app' folder:
from app.graph import app

async def run_test():
    # Define the initial state for the system
    # This simulates a real user request
    inputs = {
        "user_query": "Find me 3 new hotel or luxury condo projects in Hawaii > $1M. I sell window shades.",
        "retry_count": 0,
        "final_leads": [],
        "raw_data": [],
        "candidate_urls": []
    }
    
    print("🚀 INITIALIZING SHIIMAN INTELLIGENCE V2...")
    print(f"🔍 Task: {inputs['user_query']}")
    print("-" * 50)

    # 3. Stream the nodes as they finish to see the "Thinking" process
    # This is exactly how your chatbot will show progress to the user
    async for output in app.astream(inputs):
        for key, value in output.items():
            print(f"\n[AGENT] --- {key} Finished ---")
            
            if key == "scout_node":
                print(f"📍 Industry Identified: {value.get('industry')}")
                print(f"🔗 Sources Found: {len(value.get('candidate_urls', []))}")
            
            elif key == "hunter_node":
                print(f"📦 Raw Data Collected: {len(value.get('raw_data', []))} items")
            
            elif key == "architect_node":
                leads = value.get("final_leads", [])
                print(f"✅ Leads Finalized: {len(leads)}")
                for i, lead in enumerate(leads):
                    print(f"   {i+1}. {lead.company_name} | {lead.location} | Budget: {lead.budget}")
                    print(f"      Status: {lead.status}")

    print("\n🏁 TEST COMPLETE.")

if __name__ == "__main__":
    # Ensure dependencies are installed: pip install asyncio python-dotenv
    try:
        asyncio.run(run_test())
    except Exception as e:
        print(f"❌ TEST FAILED: {str(e)}")