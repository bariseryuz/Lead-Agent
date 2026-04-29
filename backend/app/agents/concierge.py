import os
import json
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_anthropic import ChatAnthropic
import google.generativeai as genai

# 1. FIXED SCHEMA: Added the missing fields so the code doesn't crash
class SearchSchema(BaseModel):
    industry: str = Field(description="The core business niche (e.g., Blinds, HVAC, etc.)")
    location: str = Field(description="The geographic focus (City, State, or National)")
    
    # NEW: These must be in the schema for the AI to fill them!
    requires_signals: bool = Field(default=True, description="Always True for Shiiman Leads.")
    signal_trigger: str = Field(description="The specific event to hunt for (e.g., New Construction, Funding)")
    
    source_type: str = Field(description="'Technical' (for specific State/City permits) or 'General' (for National/Web search)")
    
    search_queries: List[str] = Field(description="3-5 optimized search strings for Tavily/Serper")
    reasoning: str = Field(description="Why this specific strategy was chosen.")

def generate_search_schema(user_input: str):
    # Spend guard: cap output tokens per call (defaults conservative).
    # You can override via Railway env var `CONCIERGE_MAX_TOKENS`.
    max_tokens = int(os.getenv("CONCIERGE_MAX_TOKENS", "500"))

    # 2. OPTIMIZED PROMPT: Grouped triggers for better reasoning
    system_prompt = """STRATEGY RULES:
    1. SOURCE ROUTING:
       - Choose 'Technical' ONLY if the lead depends on government-regulated construction (HVAC, Solar, Roofing, Blinds for new builds).
       - Choose 'General' for everything else (Retail, Coffee Shops, SaaS, Tech, General Services). Even if a State is mentioned, 'General' is faster for retail/service signals.
    
    2. SIGNAL IDENTIFICATION:
       - For 'Coffee Shops' or 'Retail': The signal is 'Coming Soon' 'announcements', 'Grand Opening' 'news', or 'New Google Maps Listings' .
       - For 'Construction/Installation': The signal is 'New Building Permits' or 'Contract Awards' , 'Groundbreaking'. ,'Project Starts' , 'Requested Permits' , 'Installation Updates' , 'Completed Installations' , 'New Construction' , 'New Construction Permits' , 'New Construction Contracts' , 'New Construction Awards' , 'New Construction Groundbreaking' , 'New Construction Project Starts' , 'New Construction Requested Permits' , 'New Construction Installation Updates' , 'New Construction Completed Installations' , 'New Construction New Construction' , 'New Construction New Construction Permits' , 'New Construction New Construction Contracts' , 'New Construction New Construction Awards' , 'New Construction New Construction Groundbreaking' , 'New Construction New Construction Project Starts' , 'New Construction New Construction Requested Permits' , 'New Construction New Construction Installation Updates' , 'New Construction New Construction Completed Installations'
       - For 'B2B/Software': The signal is 'Funding' or 'Hiring Spikes' 'new' , 'Offer', 'Hiring' , 'Executive Hiring' , 'New Product Launch' , 'New Feature Release' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch' , 'New Product Launch'
    
    3. ACCURACY VS. SPEED:
       - Technical is for 99% accuracy on "Heavy" jobs.
       - General is for "Extreme Speed" on "Business Growth" jobs.


    """
    # Prefer Gemini for Concierge if configured (user requested).
    gemini_key = os.getenv("gemini") or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if gemini_key:
        genai.configure(api_key=gemini_key)
        gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        model = genai.GenerativeModel(gemini_model)

        prompt = (
            f"{system_prompt}\n\n"
            "Return ONLY valid JSON that matches this schema exactly:\n"
            f"{SearchSchema.model_json_schema()}\n\n"
            f"User Request: {user_input}\n"
        )

        resp = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0,
                "max_output_tokens": max_tokens,
                "response_mime_type": "application/json",
            },
        )
        text = (getattr(resp, "text", None) or "").strip()
        if not text:
            raise RuntimeError("Gemini returned empty response")
        try:
            payload = json.loads(text)
        except Exception:
            # Some SDK versions wrap JSON in markdown fences; try to strip.
            cleaned = text.strip().removeprefix("```json").removesuffix("```").strip()
            payload = json.loads(cleaned)
        return SearchSchema.model_validate(payload)

    # Fallback: Claude (Anthropic)
    key = os.getenv("claude") or os.getenv("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError("Missing LLM key (set `gemini` or `claude` in env).")

    model_name = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-latest")
    llm = ChatAnthropic(
        model=model_name,
        temperature=0,
        anthropic_api_key=key,
        max_tokens=max_tokens,
    )
    structured_llm = llm.with_structured_output(SearchSchema)
    return structured_llm.invoke(f"{system_prompt}\n\nUser Request: {user_input}")

if __name__ == "__main__":
    # --- TEST CASE ---
    user_query = "I want blind and shade leads in Texas and I want to target the entire United States"
    plan = generate_search_schema(user_query)

    # These will now work because they are in the SearchSchema class
    print(f"--- SHIIMAN EXECUTION PLAN ---")
    print(f"Industry: {plan.industry}")
    print(f"Location: {plan.location}")
    print(f"Signals Needed: {plan.requires_signals}")
    print(f"Signal Trigger: {plan.signal_trigger}")
    print(f"Source Type: {plan.source_type}")
    print(f"Reasoning: {plan.reasoning}")
    print(f"Queries: {plan.search_queries}")