import os
import json
from typing import Dict, List
import google.generativeai as genai
from app.models.state import AgentState
from app.models.schema import Lead, LeadReport, LeadStatus

# Setup Gemini 2.0
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash")

async def architect_node(state: AgentState) -> Dict:
    """
    Agent C: The Architect. 
    Processes Hunter's raw data into structured leads. 
    Implements 'Graceful Degradation' instead of destroying partial data.
    """
    raw_data_list = state.get("raw_data", [])
    user_query = state["user_query"]
    
    if not raw_data_list:
        print("⚠️ No raw data to analyze.")
        return {"final_leads": [], "retry_count": state.get("retry_count", 0) + 1}

    context_blob = "\n---\n".join(raw_data_list)

    prompt = f"""
    You are a Senior Sales Intelligence Architect. 
    User Query: "{user_query}"
    
    TASK:
    Extract potential business leads from the provided raw data. 
    
    ACCURACY PROTOCOL:
    1. If a row has a Project Name and Budget but missing a Company/Address, set status to 'requires_enrichment'.
    2. Do NOT use platform names (Socrata, ArcGIS, Esri) as the 'company_name'.
    3. If the valuation is a string like '$1.2M', convert it to the number 1200000.
    4. Provide a 'why_this_lead' explanation focused on the user's specific intent.

    DATA:
    {context_blob}

    Return a JSON object matching the LeadReport schema (a list of leads).
    """

    try:
        # 1. LLM Extraction
        response = model.generate_content(
            prompt, 
            generation_config={"response_mime_type": "application/json"}
        )
        
        raw_leads = json.loads(response.text).get("leads", [])
        processed_leads = []

        # 2. Deterministic Validation (The "Senior Engineer" Layer)
        for data in raw_leads:
            lead = Lead(**data)
            
            # RULE: Clean platform noise
            platforms = ["socrata", "arcgis", "esri", "tyler tech", "opendata"]
            if lead.company_name and any(p in lead.company_name.lower() for p in platforms):
                lead.company_name = None

            # RULE: Determine if it's Ready or needs Research
            if not lead.company_name or not lead.location:
                if lead.budget or "Project" in lead.why_this_lead:
                    # It's a real project, just missing contact info
                    lead.status = LeadStatus.REQUIRES_ENRICHMENT
                    lead.enrichment_query = f"Find contractor and address for project: {lead.why_this_lead}"
                    lead.confidence_score = 50
                else:
                    # It's just junk data
                    lead.status = LeadStatus.TRASH
            else:
                lead.status = LeadStatus.READY
                lead.confidence_score = 90

            if lead.status != LeadStatus.TRASH:
                processed_leads.append(lead)

    except Exception as e:
        print(f"❌ Architect Error: {str(e)}")
        processed_leads = []

    print(f"✅ Architect produced {len(processed_leads)} valid signals.")

    return {
        "final_leads": processed_leads,
        "retry_count": state.get("retry_count", 0)
    }