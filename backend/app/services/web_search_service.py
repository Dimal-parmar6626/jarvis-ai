"""Web search service using Google Custom Search API and Wikipedia."""

import logging
from typing import Any, Dict, List, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class WebSearchService:
    """Integrate with Google Custom Search API and Wikipedia."""

    GOOGLE_API_URL = "https://www.googleapis.com/customsearch/v1"
    WIKI_API_URL = "https://en.wikipedia.org/api/rest_v1/page/summary"

    def __init__(self, api_key: Optional[str] = None, cse_id: Optional[str] = None):
        self.api_key = api_key or settings.GOOGLE_API_KEY
        self.cse_id = cse_id or settings.GOOGLE_CSE_ID

    async def google_search(self, query: str, num_results: int = 5) -> Dict[str, Any]:
        """Perform a Google Custom Search."""
        if not self.api_key or not self.cse_id:
            return {"success": False, "error": "Google API key or CSE ID not configured."}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    self.GOOGLE_API_URL,
                    params={"key": self.api_key, "cx": self.cse_id, "q": query, "num": num_results},
                )
                resp.raise_for_status()
                data = resp.json()
                results = [
                    {
                        "title": item.get("title"),
                        "link": item.get("link"),
                        "snippet": item.get("snippet"),
                    }
                    for item in data.get("items", [])
                ]
                return {"success": True, "query": query, "results": results}
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Google search failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def wikipedia_search(self, topic: str) -> Dict[str, Any]:
        """Fetch a Wikipedia summary for a topic."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{self.WIKI_API_URL}/{topic.replace(' ', '_')}",
                    headers={"User-Agent": "JarvisAI/1.0"},
                )
                resp.raise_for_status()
                data = resp.json()
                return {
                    "success": True,
                    "title": data.get("title"),
                    "extract": data.get("extract"),
                    "url": data.get("content_urls", {}).get("desktop", {}).get("page"),
                    "thumbnail": data.get("thumbnail", {}).get("source"),
                }
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Wikipedia search failed: %s", exc)
            return {"success": False, "error": str(exc)}
