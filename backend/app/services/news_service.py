"""News service: fetch headlines from NewsAPI."""

import logging
from typing import Any, Dict, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class NewsService:
    """Fetch news headlines using NewsAPI."""

    BASE_URL = "https://newsapi.org/v2"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.NEWS_API_KEY

    async def get_top_headlines(self, country: str = "us", category: Optional[str] = None, page_size: int = 10) -> Dict[str, Any]:
        """Fetch top headlines."""
        if not self.api_key:
            return {"success": False, "error": "NewsAPI key not configured."}
        try:
            params: Dict[str, Any] = {
                "country": country,
                "pageSize": page_size,
                "apiKey": self.api_key,
            }
            if category:
                params["category"] = category
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{self.BASE_URL}/top-headlines", params=params)
                resp.raise_for_status()
                data = resp.json()
                articles = [
                    {
                        "title": a.get("title"),
                        "description": a.get("description"),
                        "url": a.get("url"),
                        "source": a.get("source", {}).get("name"),
                        "published_at": a.get("publishedAt"),
                    }
                    for a in data.get("articles", [])
                ]
                return {"success": True, "articles": articles, "total": data.get("totalResults", 0)}
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("News fetch failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def search_news(self, query: str, page_size: int = 10) -> Dict[str, Any]:
        """Search for news articles by query."""
        if not self.api_key:
            return {"success": False, "error": "NewsAPI key not configured."}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{self.BASE_URL}/everything",
                    params={"q": query, "pageSize": page_size, "apiKey": self.api_key, "sortBy": "relevancy"},
                )
                resp.raise_for_status()
                data = resp.json()
                articles = [
                    {
                        "title": a.get("title"),
                        "description": a.get("description"),
                        "url": a.get("url"),
                        "source": a.get("source", {}).get("name"),
                        "published_at": a.get("publishedAt"),
                    }
                    for a in data.get("articles", [])
                ]
                return {"success": True, "articles": articles, "query": query}
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("News search failed: %s", exc)
            return {"success": False, "error": str(exc)}
