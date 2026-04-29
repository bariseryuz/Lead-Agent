import datetime
import asyncio # ADDED for speed
import os
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

# --- 1. DATA MODELS (The Schema) ---
class SignalInference(BaseModel):
    event_summary: str = Field(description="Signal A: Summary of the raw event found.")
    hidden_need: str = Field(description="Signal B: The invisible problem this event creates.")
    target_persona: str = Field(description="Signal C: Exact job title of the decision maker.")
    verification_step: str = Field(description="Signal D: What the Hunter must verify for 99% accuracy.")
    confidence_score: float = Field(description="Score from 0.0 to 1.0. If below 0.85, the lead is discarded.")
    velocity: str = Field(description="The pace of the company: FAST, STEADY, or STALE.")
    suggested_search_queries: List[str] = Field(description="Search strings for the Hunter Agent.")

# --- 2. THE SIGNAL ENGINE ---
class SignalEngine:
    def __init__(self, api_key: Optional[str] = None):
        # Railway env var requested by user: `claude`
        resolved_key = api_key or os.getenv("claude") or os.getenv("ANTHROPIC_API_KEY")
        if not resolved_key:
            raise RuntimeError("Missing Anthropic API key (set `claude` in env).")

        # Spend guard: cap output tokens per call (defaults conservative).
        # You can override via Railway env var `SIGNAL_MAX_TOKENS`.
        max_tokens = int(os.getenv("SIGNAL_MAX_TOKENS", "600"))
        model_name = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-latest")
        self.llm = ChatAnthropic(
            model=model_name,
            anthropic_api_key=resolved_key,
            temperature=0,
            max_tokens=max_tokens,
        )
        self.parser = PydanticOutputParser(pydantic_object=SignalInference)

    def calculate_pace(self, event_date_str: str) -> str:
        try:
            # Logic: determines 'Pace' based on date
            event_date = datetime.datetime.strptime(event_date_str, "%Y-%m-%d")
            days_diff = (datetime.datetime.now() - event_date).days
            if days_diff <= 7: return "FAST"
            elif days_diff <= 30: return "STEADY"
            else: return "STALE"
        except Exception:
            return "STEADY"

    # CHANGED TO ASYNC for Parallel Processing
    async def process_raw_data(self, target_industry: str, raw_event: str, event_date: str = None) -> SignalInference:
        pace_check = self.calculate_pace(event_date) if event_date else "STEADY"

        system_prompt = """
        You are the Shiiman Intelligence Engine. You transform Raw Data into High-Intent Lead Plans.
        
        INPUT:
        Industry: {industry}
        Raw Event: {event}
        
        TASK:
        1. Analyze Signal A (The Event).
        2. Infer Signal B (The Hidden Need): Why does this event make them need {industry}?
        3. Identify Signal C (The Persona): Who buys this?
        4. Set Signal D (The Verification): How do we prove this is 99% accurate?
        
        {format_instructions}
        """

        prompt = ChatPromptTemplate.from_template(system_prompt)
        chain = prompt | self.llm | self.parser

        # invoke is now awaited
        result = await chain.ainvoke({
            "industry": target_industry,
            "event": raw_event,
            "format_instructions": self.parser.get_format_instructions()
        })

        if pace_check == "STALE":
            result.velocity = "STALE"
            result.confidence_score = result.confidence_score * 0.5 
            
        return result

# --- 3. WHY THIS IS PERFECT FOR YOU ---
"""
1. ACCURACY: It uses Claude 3.5 Sonnet to 'Think' through the lead.
2. FILTERING: The confidence_score allows you to kill bad leads automatically.
3. SIGNALS: It handles Signal A, B, C, and D in one single pass.
4. HUNTER PREP: It provides 'suggested_search_queries' so the Technical Hunter 
   knows exactly what to look for on ArcGIS or LinkedIn.
"""