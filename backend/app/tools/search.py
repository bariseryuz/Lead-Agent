import os
import asyncio
from typing import Iterable, List, Optional

import httpx


async def _tavily_search_one(
    client: httpx.AsyncClient,
    *,
    api_key: str,
    query: str,
    max_results: int = 10,
    search_depth: str = "basic",
) -> List[str]:
    resp = await client.post(
        "https://api.tavily.com/search",
        json={
            "api_key": api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": search_depth,
            "include_answer": False,
            "include_raw_content": False,
        },
        timeout=30.0,
    )
    resp.raise_for_status()
    data = resp.json()
    results = data.get("results", []) or []
    urls: List[str] = []
    for r in results:
        url = (r or {}).get("url")
        if url:
            urls.append(url)
    return urls


async def tavily_search_urls(
    queries: Iterable[str],
    *,
    api_key: Optional[str] = None,
    max_results_per_query: int = 10,
    search_depth: str = "basic",
) -> List[str]:
    """
    Tavily search for multiple queries and return unique URLs.
    Requires `TAVILY_API_KEY` (or pass api_key=...).
    """
    key = api_key or os.getenv("TAVILY_API_KEY")
    if not key:
        raise RuntimeError("Missing TAVILY_API_KEY")

    q_list = [q.strip() for q in queries if q and q.strip()]
    if not q_list:
        return []

    async with httpx.AsyncClient() as client:
        tasks = [
            _tavily_search_one(
                client,
                api_key=key,
                query=q,
                max_results=max_results_per_query,
                search_depth=search_depth,
            )
            for q in q_list
        ]
        url_lists = await asyncio.gather(*tasks)

    deduped: List[str] = []
    seen = set()
    for urls in url_lists:
        for u in urls:
            if u not in seen:
                seen.add(u)
                deduped.append(u)
    return deduped

