"""Web Research Agent - Gathers competitive intelligence from the web."""

import os
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

Analyze the search results and extract:
1. Product features and capabilities
2. Pricing information (plans, pricing tiers)
3. Target market and use cases
4. Strengths and unique selling points
5. Customer sentiment from reviews

Be factual and cite sources. If information isn't found, say so clearly."""),
            ("human", """Company: {company}
Query: {query}

Search Results:
{search_results}

Provide a structured analysis in this format:

## Product Overview
[Brief description]

## Key Features
- Feature 1
- Feature 2
...

## Pricing
[Pricing information if found, or "Not found in search results"]

## Target Market
[Who uses this product]

## Strengths
- Strength 1
- Strength 2

## Recent News
[Recent developments if any]

## Sources
[List URLs]
""")
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

            # Research this company
            company_data = await self._research_company(company, query)
            findings.append(company_data)
            profiles[company] = company_data

        await self._emit_status("running", 95, "Finalizing research...")

        # Track cost
        total_text = " ".join([str(f) for f in findings])
        cost_info = self._track_cost(query, total_text)

        return {
            "research_findings": findings,
            "competitor_profiles": profiles,
            "current_agent": self.name,
            "current_phase": "research",
            "cost_tracking": {
                **state.get("cost_tracking", {}),
                self.name: cost_info
            }
        }

    async def _research_company(self, company: str, query: str) -> Dict[str, Any]:
        """Research a single company.

        Args:
            company: Company name
            query: User's original query

        Returns:
            Dictionary with research findings
        """
        # Build search queries
        search_queries = [
            f"{company} product features pricing",
            f"{company} vs competitors review",
            f"{company} recent news updates"
        ]

        all_results = []

        # Execute searches
        for search_query in search_queries[:2]:  # Limit to 2 queries per company
            results = await self.search_manager.search(
                query=search_query,
                max_results=3
            )
            all_results.extend(results)

        # Check RAG for existing research (if available)
        rag_info = ""
        if self.rag_client:
            try:
                rag_response = await self.rag_client.query(
                    question=f"What do you know about {company}?",
                    max_chunks=2
                )
                if rag_response.get("success"):
                    rag_info = f"\n\nExisting Knowledge: {rag_response.get('answer', '')}"
            except:
                pass  # RAG is optional

        # Format search results for LLM
        formatted_results = "\n\n".join([
            f"[{r['source'].upper()}] {r['title']}\n{r['content']}\nURL: {r['url']}"
            for r in all_results[:10]  # Limit to 10 results
        ])

        # Analyze with LLM
        messages = self.analysis_prompt.format_messages(
            company=company,
            query=query,
            search_results=formatted_results + rag_info
        )

        response = await self.llm.ainvoke(messages)
        analysis = response.content if hasattr(response, 'content') else str(response)

        return {
            "company": company,
            "analysis": analysis,
            "search_results": all_results,
            "sources": [r["url"] for r in all_results],
            "agent": self.name
        }
