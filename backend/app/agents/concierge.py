import os
import json
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_anthropic import ChatAnthropic
from google import genai
import time
import sys

# Move this to the left (no indentation)
class SearchSchema(BaseModel):
    industry: str
    location: str
    requires_signals: bool = True
    signal_trigger: str
    source_type: str
    search_queries: List[str]
    reasoning: str

def _dbg(hypothesis_id: str, location: str, message: str, data: dict, run_id: str = "pre-fix"):
    try:
        payload = {
            "sessionId": "c8eaed",
            "runId": run_id,
            "hypothesisId": hypothesis_id,
            "location": location,
            "message": message,
            "data": data,
            "timestamp": int(time.time() * 1000),
        }
        line = json.dumps(payload, ensure_ascii=False)

        # Always emit to stderr so remote hosts capture it.
        try:
            print(line, file=sys.stderr, flush=True)
        except Exception:
            pass

        # Also write to local Cursor debug log when available (local runs).
        log_path = os.getenv(
            "CURSOR_DEBUG_LOG_PATH",
            "/Users/bariseryuz/Documents/GitHub/Lead-Agent/.cursor/debug-c8eaed.log",
        )
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass
    except Exception:
        pass

#region agent log
_dbg(
    "A",
    "backend/app/agents/concierge.py:module_import",
    "module imported",
    {"pid": os.getpid()},
)
#endregion

def generate_search_schema(user_input: str):
    max_tokens = int(os.getenv("CONCIERGE_MAX_TOKENS", "500"))

    #region agent log
    _dbg(
        "A",
        "backend/app/agents/concierge.py:generate_search_schema",
        "entered",
        {
            "user_input_len": len(user_input or ""),
            "max_tokens": max_tokens,
        },
    )
    #endregion

    system_prompt = """ROLE: You are a Lead Generation Architect. Your goal is to map user requests to the most effective "hunt" strategy.

    1. SOURCE ROUTING LOGIC:
       - 'Technical': Use when leads are verified via regulatory data, government filings, or infrastructure changes. (e.g., HVAC, Solar, Electricians, Roofing, specialized medical equipment).
       - 'General': Use for business growth indicators, marketing signals, or general service expansions. (e.g., Retail, SaaS, Professional Services, Hospitality).

    2. SIGNAL CATEGORIES:
       - INFRASTRUCTURE: New Building Permits, Site Renovations, Groundbreaking (Target: Construction/Trades).
       - MARKET GROWTH: 'Coming Soon' announcements, Grand Openings, New Google Maps listings (Target: Retail/Local Biz).
       - CORPORATE MOMENTUM: Series A-D Funding, Executive Hiring, Office Relocations (Target: B2B/SaaS).
       - REGULATORY/LEGAL: New Business Licenses, Professional Certifications issued (Target: High-end Services).

    3. QUERY CONSTRUCTION:
       - Create 3-5 high-intent search strings.
       - Use specific proximity keywords (e.g., 'recently filed', 'announcing new location', 'breaking ground').
    """

    # GEMINI ATTEMPT
    gemini_key = os.getenv("gemini") or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    #region agent log
    _dbg(
        "D",
        "backend/app/agents/concierge.py:generate_search_schema",
        "resolved keys",
        {
            "has_gemini_key": bool(gemini_key),
            "has_claude_key": bool(os.getenv("claude") or os.getenv("ANTHROPIC_API_KEY")),
            "gemini_model": os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
            "claude_model": os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-latest"),
        },
    )
    #endregion
    if gemini_key:
        try:
            client = genai.Client(api_key=gemini_key)
            # Add schema to prompt for better accuracy
            prompt = f"{system_prompt}\nReturn JSON matching this schema: {SearchSchema.model_json_schema()}\nUser Request: {user_input}"
            
            resp = client.models.generate_content(
                model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
                contents=prompt,
                config={
                    "temperature": 0,
                    "max_output_tokens": max_tokens,
                    "response_mime_type": "application/json",
                },
            )
            if resp.text:
                #region agent log
                _dbg(
                    "B",
                    "backend/app/agents/concierge.py:generate_search_schema",
                    "gemini response received",
                    {
                        "resp_text_len": len(resp.text),
                    },
                )
                #endregion
                return SearchSchema.model_validate(json.loads(resp.text))
        except Exception as e:
            #region agent log
            _dbg(
                "B",
                "backend/app/agents/concierge.py:generate_search_schema",
                "gemini failed",
                {
                    "error_type": type(e).__name__,
                },
            )
            #endregion
            print(f"Gemini failed, trying Claude: {e}")

    # CLAUDE FALLBACK
    key = os.getenv("claude") or os.getenv("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError("No LLM keys found.")

    llm = ChatAnthropic(
        model=os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-latest"),
        temperature=0,
        anthropic_api_key=key,
        max_tokens=max_tokens,
    ).with_structured_output(SearchSchema)
    
    #region agent log
    _dbg(
        "C",
        "backend/app/agents/concierge.py:generate_search_schema",
        "invoking claude structured output",
        {},
    )
    #endregion
    return llm.invoke(f"{system_prompt}\n\nUser Request: {user_input}")