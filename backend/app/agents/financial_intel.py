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
        super().__init__(name="Financial Intelligence Agent", llm=llm, **kwargs)
        self.search_manager = SearchManager(tavily_api_key)

        # Prompt for analyzing financial data
        self.analysis_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are a financial analyst researching company data.

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
- Keep concise and structured""",
                ),
                (
                    "human",
                    """Company: {company}

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

Follow this structure exactly with proper markdown formatting.""",
                ),
            ]
        )

    async def _process(self, state: MarketResearchState) -> Dict[str, Any]:
        """Research financial data for companies.

        Args:
            state: Current workflow state

        Returns:
            State updates with financial data
        """
        companies = state.get("companies", [])

        await self._emit_status(
            "running",
            10,
            f"Researching financial data for {len(companies)} companies...",
        )

        financial_data = {}

        for idx, company in enumerate(companies):
            progress = 10 + (idx / len(companies)) * 80

            await self._emit_status(
                "running", int(progress), f"Researching {company} financials..."
            )

            # Get financial priorities from coordinator (or use defaults)
            financial_priorities = state.get("financial_priorities", [])
            if financial_priorities:
                # Use coordinator's prioritized metrics
                metrics_str = " ".join(financial_priorities[:5])
                search_query = f"{company} {metrics_str}"
                print(
                    f"[i] Using coordinator's financial priorities for {company}: {financial_priorities[:5]}"
                )
            else:
                # Fallback to default financial queries
                search_query = f"{company} funding valuation revenue team size"
                print(f"[i] Using default financial query for {company}")

            # Get depth setting from coordinator
            depth_settings = state.get("depth_settings", {})
            financial_depth = depth_settings.get("financial_intel", "standard")

            # Adjust search depth based on coordinator's guidance
            max_results = {"light": 2, "standard": 3, "comprehensive": 5}.get(
                financial_depth, 3
            )

            results = await self.search_manager.search(
                search_query, max_results=max_results
            )

            # For comprehensive depth, scrape top URL for full financial details
            if financial_depth == "comprehensive" and results:
                # Scrape top URL for complete financial context
                top_url = results[0]["url"]
                print(f"[i] Comprehensive depth: Scraping {top_url} for full financial details")

                scraped = await self.search_manager.scrape_url(top_url)
                if scraped.get("success"):
                    # Add scraped content as additional result
                    results.append({
                        "title": f"Full Content: {scraped['title']}",
                        "url": top_url,
                        "content": scraped["content"],
                        "score": 1.0,
                        "source": "scraped"
                    })
                    print(f"[i] Scraped {len(scraped['content'])} chars for financial details")
                else:
                    print(f"[!] Failed to scrape {top_url}: {scraped.get('error', 'Unknown')}")

            # Format results
            formatted_results = "\n\n".join(
                [
                    f"[{r['source'].upper()}] {r['title']}\n{r['content']}"
                    for r in results
                ]
            )

            # Analyze with LLM
            messages = self.analysis_prompt.format_messages(
                company=company, search_results=formatted_results
            )

            response = await self.llm.ainvoke(messages)
            analysis = (
                response.content if hasattr(response, "content") else str(response)
            )

            # Track cost for this specific company
            input_text = f"{company}\n{formatted_results}"
            company_cost = self._track_cost(input_text, analysis)

            financial_data[company] = {
                "analysis": analysis,
                "sources": [r["url"] for r in results],
                "company": company,
                "cost_info": company_cost  # Include cost tracking for this company
            }

        await self._emit_status("running", 95, "Finalizing financial research...")

        # Aggregate per-company costs for accurate total tracking
        total_input_tokens = 0
        total_output_tokens = 0
        total_cost = 0.0

        for company_data in financial_data.values():
            if "cost_info" in company_data:
                company_cost = company_data["cost_info"]
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
            "timestamp": list(financial_data.values())[0]["cost_info"]["timestamp"] if financial_data else 0,
            "companies_researched": len(companies)
        }

        return {
            "financial_data": financial_data,
            "current_agent": [self.name],  # List for operator.add (parallel-safe)
            # Don't update current_phase (Web Research sets it, both agents in same phase)
            "cost_tracking": [cost_info],  # List for operator.add (parallel-safe)
        }
