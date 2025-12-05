"""Search tools: Tavily, DuckDuckGo, and web scraping."""

from typing import List, Dict, Any, Optional
from tavily import TavilyClient
from ddgs import DDGS
import requests
from bs4 import BeautifulSoup
from ..state import MarketResearchState
from app.services.cache import search_cache


# Tavily Search Tool
class TavilySearch:
    """Tavily search for high-quality web results."""

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("TAVILY_API_KEY required")
        self.client = TavilyClient(api_key=api_key)

    async def search(
        self,
        query: str,
        max_results: int = 5,
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Search using Tavily API.

        Args:
            query: Search query
            max_results: Maximum number of results
            include_domains: Domains to include
            exclude_domains: Domains to exclude

        Returns:
            List of search results with title, url, content
        """
        try:
            response = self.client.search(
                query=query,
                max_results=max_results,
                include_domains=include_domains,
                exclude_domains=exclude_domains,
                search_depth="advanced"
            )

            results = []
            for result in response.get("results", []):
                results.append({
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "content": result.get("content", ""),
                    "score": result.get("score", 0.0),
                    "source": "tavily"
                })

            return results

        except Exception as e:
            print(f"Tavily search error: {e}")
            return []


# DuckDuckGo Search Tool (fallback)
class DuckDuckGoSearch:
    """DuckDuckGo search as free fallback."""

    def __init__(self):
        self.ddgs = DDGS()

    async def search(
        self,
        query: str,
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Search using DuckDuckGo.

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            List of search results
        """
        try:
            results = []
            for result in self.ddgs.text(query, max_results=max_results):
                results.append({
                    "title": result.get("title", ""),
                    "url": result.get("href", ""),
                    "content": result.get("body", ""),
                    "source": "duckduckgo"
                })

            return results

        except Exception as e:
            print(f"DuckDuckGo search error: {e}")
            return []


# Web Scraper
class WebScraper:
    """Simple web scraper using requests + BeautifulSoup."""

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    async def scrape(self, url: str, max_length: int = 5000) -> Dict[str, Any]:
        """Scrape content from a URL.

        Args:
            url: URL to scrape
            max_length: Maximum content length

        Returns:
            Dictionary with title and content
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            # Remove script and style tags
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()

            # Extract title
            title = soup.title.string if soup.title else ""

            # Extract text content
            text = soup.get_text(separator="\n", strip=True)

            # Clean up text
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            content = "\n".join(lines)[:max_length]

            return {
                "url": url,
                "title": title,
                "content": content,
                "success": True
            }

        except Exception as e:
            return {
                "url": url,
                "title": "",
                "content": "",
                "error": str(e),
                "success": False
            }


# Unified search function
class SearchManager:
    """Manages search tools with fallback logic."""

    def __init__(self, tavily_api_key: Optional[str] = None):
        self.tavily = TavilySearch(tavily_api_key) if tavily_api_key else None
        self.ddg = DuckDuckGoSearch()
        self.scraper = WebScraper()

    async def search(
        self,
        query: str,
        max_results: int = 5,
        use_tavily: bool = True,
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Search with Tavily first, fallback to DuckDuckGo. Uses Redis cache.

        Args:
            query: Search query
            max_results: Maximum results
            use_tavily: Try Tavily first if available
            include_domains: Domains to include
            exclude_domains: Domains to exclude

        Returns:
            Search results (from cache or API)
        """
        # Check cache first (5-10x faster, saves Tavily quota)
        cached_results = search_cache.get(
            query,
            max_results,
            include_domains,
            exclude_domains
        )
        if cached_results:
            return cached_results

        # Cache miss - fetch from API
        results = []

        # Try Tavily first (better quality)
        if use_tavily and self.tavily:
            results = await self.tavily.search(
                query,
                max_results,
                include_domains,
                exclude_domains
            )

        # Fallback to DuckDuckGo if Tavily fails (free, unlimited)
        if not results:
            results = await self.ddg.search(query, max_results)

        # Cache the results for future requests
        if results:
            search_cache.set(
                query,
                results,
                max_results,
                include_domains,
                exclude_domains
            )

        return results

    async def scrape_url(self, url: str) -> Dict[str, Any]:
        """Scrape content from URL."""
        return await self.scraper.scrape(url)
