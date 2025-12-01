"""Financial Intelligence Agent - Gathers company financial data."""

from typing import Dict, Any
from langchain_core.language_models import BaseLLM
from langchain_core.prompts import ChatPromptTemplate
from .base import BaseAgent
from .state import MarketResearchState
from .tools.search import SearchManager


class FinancialIntelligenceAgent(BaseAgent):
    """Agent that researches company financial information.

    Gathers:
    - Funding rounds and valuations
    - Revenue estimates
    - Team size and growth
    - Investor information
    - Recent financial news
    """

    def __init__(self, llm: BaseLLM, tavily_api_key: str = None, **kwargs):
        super().__init__(
            name="Financial Intelligence Agent",
            llm=llm,
            **kwargs
        )
        self.search_manager = SearchManager(tavily_api_key)

        # Prompt for analyzing financial data
        self.analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a financial analyst researching company data.

CRITICAL: Output MUST be in clean markdown format with proper structure.

Extract and structure:
1. Funding: Rounds, amounts, investors, valuations
2. Revenue: Estimates, growth trends
3. Team: Size, growth rate
4. Market traction: Users, customers, metrics
5. Recent developments

Be factual. If data not found, state clearly "Not found in search results."

FORMATTING RULES:
- Use ## for section headers (H2)
- Use - for bullet lists
- Add blank line after headers
- Add blank line between sections
- Use **bold** for key numbers/amounts
- Keep concise and structured"""),
            ("human", """Company: {company}

Search Results:
{search_results}

Provide financial analysis using this EXACT format:

## Funding & Investment

[Funding rounds, amounts, investors, or "Not found in search results"]

## Revenue & Growth

[Revenue estimates, growth trends, or "Not found in search results"]

## Team Size & Growth

[Team size, growth rate, or "Not found in search results"]

## Market Traction

[Users, customers, key metrics, or "Not found in search results"]

## Recent Developments

[Recent financial news, acquisitions, partnerships, or "No recent developments found"]

Follow this structure exactly with proper markdown formatting.""")
        ])

    async def _process(self, state: MarketResearchState) -> Dict[str, Any]:
        """Research financial data for companies.

        Args:
            state: Current workflow state

        Returns:
            State updates with financial data
        """
        companies = state.get("companies", [])

        await self._emit_status("running", 10, f"Researching financial data for {len(companies)} companies...")

        financial_data = {}

        for idx, company in enumerate(companies):
            progress = 10 + (idx / len(companies)) * 80

            await self._emit_status("running", int(progress), f"Researching {company} financials...")

            # Search for financial info
            search_query = f"{company} funding valuation revenue team size"
            results = await self.search_manager.search(search_query, max_results=3)

            # Format results
            formatted_results = "\n\n".join([
                f"[{r['source'].upper()}] {r['title']}\n{r['content']}"
                for r in results[:5]
            ])

            # Analyze with LLM
            messages = self.analysis_prompt.format_messages(
                company=company,
                search_results=formatted_results
            )

            response = await self.llm.ainvoke(messages)
            analysis = response.content if hasattr(response, 'content') else str(response)

            financial_data[company] = {
                "analysis": analysis,
                "sources": [r["url"] for r in results],
                "company": company
            }

        await self._emit_status("running", 95, "Finalizing financial research...")

        # Track cost
        all_data = " ".join([d["analysis"] for d in financial_data.values()])
        cost_info = self._track_cost("", all_data)

        return {
            "financial_data": financial_data,
            "current_agent": self.name,
            "current_phase": "research",
            "cost_tracking": {
                **state.get("cost_tracking", {}),
                self.name: cost_info
            }
        }
