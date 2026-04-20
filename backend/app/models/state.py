from typing import List, TypedDict

from app.models.schema import Lead


class AgentState(TypedDict, total=False):
    user_query: str
    retry_count: int
    industry: str
    search_queries: List[str]
    candidate_urls: List[str]
    raw_data: List[str]
    final_leads: List[Lead]
