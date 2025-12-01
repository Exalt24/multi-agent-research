"""Data Analyst Agent - Creates comparative analysis and SWOT."""

from typing import Dict, Any, List
from langchain_core.language_models import BaseLLM
from langchain_core.prompts import ChatPromptTemplate
from .base import BaseAgent
from .state import MarketResearchState


class DataAnalystAgent(BaseAgent):
    """Agent that analyzes research data and creates comparisons.

    Produces:
    - Feature comparison matrix
    - Pricing comparison
    - SWOT analysis per company
    - Market positioning insights
    - Competitive advantages
    """

    def __init__(self, llm: BaseLLM, **kwargs):
        super().__init__(
            name="Data Analyst Agent",
            llm=llm,
            **kwargs
        )

        # Prompt template for comparative analysis
        self.analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a data analyst specializing in competitive analysis.

CRITICAL: Use STRICT markdown formatting with proper tables and structure.

Analyze the research data and create a comprehensive comparison:

1. Feature Comparison Matrix (table format)
2. Pricing Comparison (if available)
3. SWOT Analysis for each company
4. Market Positioning insights
5. Competitive Advantages summary

FORMATTING RULES:
- Use ## for main sections (H2)
- Use ### for subsections (H3)
- Use proper markdown tables with | separators
- Add blank lines between sections
- Use **bold** for labels
- Use - for bullet points
- Ensure tables are properly formatted with header row and separator row"""),
            ("human", """Companies: {companies}

Research Data:
{research_data}

Create a comprehensive competitive analysis using this EXACT structure:

## Feature Comparison Matrix

| Feature | {company_list} |
|---------|{separator}|
| Feature 1 | Company A value | Company B value |
| Feature 2 | Company A value | Company B value |

(Add 5-7 key features based on research)

## Pricing Comparison

[Comparison table or text if data available, or "Insufficient pricing data in research results"]

## SWOT Analysis

### Company 1

**Strengths:**
- Strength 1
- Strength 2

**Weaknesses:**
- Weakness 1
- Weakness 2

**Opportunities:**
- Opportunity 1
- Opportunity 2

**Threats:**
- Threat 1
- Threat 2

(Repeat ### Company sections for each company)

## Market Positioning

[2-3 paragraphs analyzing how each company positions itself in the market]

## Competitive Advantages

- **Company 1:** [Key advantages]
- **Company 2:** [Key advantages]
- **Company 3:** [Key advantages]

Follow this structure exactly with proper markdown formatting.""")
        ])

    async def _process(self, state: MarketResearchState) -> Dict[str, Any]:
        """Analyze research findings and create comparisons.

        Args:
            state: Current workflow state

        Returns:
            State updates with analysis
        """
        companies = state.get("companies", [])
        profiles = state.get("competitor_profiles", {})

        await self._emit_status("running", 10, f"Analyzing {len(companies)} companies...")

        # Combine all research data
        research_data = "\n\n".join([
            f"### {company}\n{profile.get('analysis', 'No data')}"
            for company, profile in profiles.items()
        ])

        # Create helper strings for prompt
        company_list = " | ".join(companies)
        separator = "|".join(["---" for _ in companies])

        await self._emit_status("running", 50, "Creating comparative analysis...")

        # Generate analysis with LLM
        messages = self.analysis_prompt.format_messages(
            companies=", ".join(companies),
            research_data=research_data,
            company_list=company_list,
            separator=separator,
            company_1=companies[0] if companies else ""
        )

        response = await self.llm.ainvoke(messages)
        analysis = response.content if hasattr(response, 'content') else str(response)

        await self._emit_status("running", 90, "Finalizing analysis...")

        # Track cost
        cost_info = self._track_cost(research_data, analysis)

        # Structure the analysis
        comparative_analysis = {
            "analysis_text": analysis,
            "companies_analyzed": companies,
            "analysis_sections": [
                "Feature Comparison",
                "Pricing Comparison",
                "SWOT Analysis",
                "Market Positioning",
                "Competitive Advantages"
            ]
        }

        return {
            "comparative_analysis": comparative_analysis,
            "current_agent": self.name,
            "current_phase": "analysis",
            "cost_tracking": {
                **state.get("cost_tracking", {}),
                self.name: cost_info
            }
        }
