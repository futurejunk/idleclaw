from __future__ import annotations

import logging

import httpx

from server.src.config import settings

logger = logging.getLogger(__name__)


async def web_search_handler(query: str) -> str:
    """Query SearXNG and return formatted top results."""
    if not settings.searxng_url:
        return "Error: Web search is not configured (SEARXNG_URL not set)."

    url = f"{settings.searxng_url}/search"
    params = {
        "q": query,
        "format": "json",
        "categories": "general",
    }

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    results = data.get("results", [])[:3]
    if not results:
        return f"No results found for: {query}"

    lines = [f"Search results for: {query}\n"]
    for i, r in enumerate(results, 1):
        title = r.get("title", "")
        snippet = r.get("content", "")
        if len(snippet) > 200:
            snippet = snippet[:200] + "..."
        lines.append(f"{i}. {title}")
        if snippet:
            lines.append(f"   {snippet}")
        lines.append("")

    return "\n".join(lines)
