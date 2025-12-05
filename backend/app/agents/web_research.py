"""Web Research Agent - Gathers competitive intelligence from the web."""

from typing import Dict, Any, List
from langchain_core.language_models import BaseLLM
from langchain_core.prompts import ChatPromptTemplate
from .base import BaseAgent
from .state import MarketResearchState
from .tools.search import SearchManager
from .tools.rag_client import RAGClient


class WebResearchAgent(BaseAgent):
    """Agent that researches companies using web search and scraping.

    Gathers:
    - Product features and capabilities
    - Pricing information
    - Customer reviews and sentiment
    - Recent news and updates
    - Company information
    """

    def __init__(
        self,
        llm: BaseLLM,
        tavily_api_key: str = None,
        rag_api_url: str = None,
        **kwargs
    ):
        super().__init__(
            name="Web Research Agent",
            llm=llm,
            **kwargs
        )
        self.search_manager = SearchManager(tavily_api_key)
        self.rag_client = RAGClient(rag_api_url) if rag_api_url else None

        # Prompt template for analyzing search results
        self.analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a web research analyst gathering competitive intelligence.

CRITICAL: Output MUST be in clean markdown format with proper structure.

Analyze the search results and extract:
1. Product features and capabilities
2. Pricing information (plans, pricing tiers)
3. Target market and use cases
4. Strengths and unique selling points
5. Customer sentiment from reviews

Be factual and cite sources. If information isn't found, say so clearly.

FORMATTING RULES:
- Use ## for section headers (H2)
- Use - for bullet lists
- Add blank line after headers
- Add blank line between sections
- Use **bold** for key terms
- Keep it concise and readable"""),
            ("human", """Company: {company}
Query: {query}

Search Results:
{search_results}

Provide a structured analysis using this EXACT format:

## Product Overview

[Brief 2-3 sentence description]

## Key Features

- Feature 1
- Feature 2
- Feature 3

## Pricing

[Pricing information, or "Not found in search results"]

## Target Market

[1-2 sentences about who uses this product]

## Strengths

- Strength 1
- Strength 2
- Strength 3

## Recent News

[Recent developments or "No recent news found"]

## Sources

- [URL 1]
- [URL 2]

Follow this structure exactly with proper markdown formatting.""")
        ])

    async def _process(self, state: MarketResearchState) -> Dict[str, Any]:
        """Research all companies in the query.

        Args:
            state: Current workflow state

        Returns:
            State updates with research findings
        """
        companies = state.get("companies", [])
        query = state.get("query", "")

        await self._emit_status("running", 10, f"Researching {len(companies)} companies...")

        findings = []
        profiles = {}

        for idx, company in enumerate(companies):
            progress = 10 + (idx / len(companies)) * 80

            await self._emit_status(
                "running",
                int(progress),
                f"Researching {company}..."
            )

            # Research this company with strategic guidance from coordinator
            company_data = await self._research_company(company, query, state)
            findings.append(company_data)
            profiles[company] = company_data

        await self._emit_status("running", 95, "Finalizing research...")

        # Aggregate per-company costs for accurate total tracking
        total_input_tokens = 0
        total_output_tokens = 0
        total_cost = 0.0

        for finding in findings:
            if "cost_info" in finding:
                company_cost = finding["cost_info"]
                total_input_tokens += company_cost.get("input_tokens", 0)
                total_output_tokens += company_cost.get("output_tokens", 0)
                total_cost += company_cost.get("estimated_cost_usd", 0.0)

        # Aggregate cost info
        cost_info = {
            "agent": self.name,
            "input_tokens": total_input_tokens,
            "output_tokens": total_output_tokens,
            "total_tokens": total_input_tokens + total_output_tokens,
            "estimated_cost_usd": total_cost,
            "model_name": self._get_model_name(),
            "timestamp": findings[0]["cost_info"]["timestamp"] if findings and "cost_info" in findings[0] else 0,
            "companies_researched": len(companies)
        }

        return {
            "research_findings": findings,
            "competitor_profiles": profiles,
            "current_agent": [self.name],  # List for operator.add (parallel-safe)
            "current_phase": "research",
            "cost_tracking": {
                **state.get("cost_tracking", {}),
                self.name: cost_info
            }
        }

    async def _research_company(self, company: str, query: str, state: MarketResearchState) -> Dict[str, Any]:
        """Research a single company using coordinator's strategic guidance.

        Args:
            company: Company name
            query: User's original query
            state: Full state with coordinator's search priorities

        Returns:
            Dictionary with research findings
        """
        # Get search priorities from coordinator (or use defaults)
        search_priorities = state.get("search_priorities", {})
        company_keywords = search_priorities.get(company, [])

        # Build search queries based on coordinator's guidance
        if company_keywords:
            # Use coordinator's strategic keywords
            search_queries = [f"{company} {keyword}" for keyword in company_keywords[:3]]
            print(f"[i] Using coordinator's search priorities for {company}: {company_keywords[:3]}")
        else:
            # Fallback to default queries if coordinator didn't specify
            search_queries = [
                f"{company} product features pricing",
                f"{company} vs competitors review",
                f"{company} recent news updates"
            ]
            print(f"[i] Using default search queries for {company} (no coordinator priorities)")

        # Get depth setting from coordinator
        depth_settings = state.get("depth_settings", {})
        web_depth = depth_settings.get("web_research", "standard")

        # Adjust number of searches based on depth
        max_queries = {"light": 2, "standard": 3, "comprehensive": 4}.get(web_depth, 3)

        all_results = []

        # Execute searches (number based on coordinator's depth setting)
        for search_query in search_queries[:max_queries]:
            # Adjust results per query based on depth
            results_per_query = {"light": 2, "standard": 3, "comprehensive": 5}.get(web_depth, 3)

            results = await self.search_manager.search(
                query=search_query,
                max_results=results_per_query
            )
            all_results.extend(results)

        # For comprehensive depth, scrape top URLs for full content (not just snippets)
        if web_depth == "comprehensive" and all_results:
            await self._emit_status("running", int(progress) + 5, f"Scraping full content for {company}...")

            # Scrape top 2 URLs for complete context
            urls_to_scrape = [r["url"] for r in all_results[:2]]
            print(f"[i] Comprehensive depth: Scraping {len(urls_to_scrape)} URLs for full content")

            for url in urls_to_scrape:
                scraped = await self.search_manager.scrape_url(url)
                if scraped.get("success"):
                    # Add scraped content as additional "result"
                    all_results.append({
                        "title": f"Full Content: {scraped['title']}",
                        "url": url,
                        "content": scraped["content"],
                        "score": 1.0,  # High priority (full content)
                        "source": "scraped"
                    })
                    print(f"[i] Scraped {len(scraped['content'])} chars from {url}")
                else:
                    print(f"[!] Failed to scrape {url}: {scraped.get('error', 'Unknown error')}")

        # Check RAG for existing research (if available)
        rag_info = ""
        if self.rag_client:
            try:
                # Adjust RAG chunks based on depth setting
                rag_chunks = {"light": 1, "standard": 2, "comprehensive": 4}.get(web_depth, 2)

                rag_response = await self.rag_client.query(
                    question=f"What do you know about {company}?",
                    max_chunks=rag_chunks
                )
                if rag_response.get("success"):
                    rag_info = f"\n\nExisting Knowledge from RAG: {rag_response.get('answer', '')}"
            except Exception as e:
                # RAG is optional, but log errors for debugging
                print(f"[!] RAG query failed for {company}: {e}")
                # Continue without RAG data (graceful degradation)

        # Format search results for LLM (adapt to depth setting)
        # Light: 5 results, Standard: 10 results, Comprehensive: 15 results
        max_results_to_use = {"light": 5, "standard": 10, "comprehensive": 15}.get(web_depth, 10)

        formatted_results = "\n\n".join([
            f"[{r['source'].upper()}] {r['title']}\n{r['content']}\nURL: {r['url']}"
            for r in all_results[:max_results_to_use]
        ])

        # Analyze with LLM
        messages = self.analysis_prompt.format_messages(
            company=company,
            query=query,
            search_results=formatted_results + rag_info
        )

        response = await self.llm.ainvoke(messages)
        analysis = response.content if hasattr(response, 'content') else str(response)

        # Track cost for this specific company
        input_text = f"{company}\n{query}\n{formatted_results}\n{rag_info}"
        company_cost = self._track_cost(input_text, analysis)

        return {
            "company": company,
            "analysis": analysis,
            "search_results": all_results,
            "sources": [r["url"] for r in all_results],
            "agent": self.name,
            "cost_info": company_cost  # Include cost tracking for this company
        }
