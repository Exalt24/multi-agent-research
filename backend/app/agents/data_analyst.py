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

MARKDOWN TABLE FORMATTING RULES (CRITICAL):
1. Each table row MUST be on its own line (use newline character \\n)
2. Never put multiple rows on the same line
3. Format: | Column 1 | Column 2 | Column 3 |
4. Header row, separator row, then data rows
5. Each row separated by newline

GENERAL FORMATTING RULES:
- Use ## for main sections (H2)
- Use ### for subsections (H3)
- Use proper markdown tables with | separators
- Add blank lines between sections
- Use **bold** for labels
- Use - for bullet points
- NEVER concatenate table rows on one line"""),
            ("human", """Companies: {companies}

Research Data:
{research_data}

Create a comprehensive competitive analysis using this EXACT structure:

## Feature Comparison Matrix

CRITICAL: Each table row must be on its OWN LINE with newline characters.

Example format (note: each row on separate line):
| Feature | {company_list} |
|---------|{separator}|
| Feature 1 | Company A value | Company B value |
| Feature 2 | Company A value | Company B value |
| Feature 3 | Company A value | Company B value |

Create a table with 5-7 key features. IMPORTANT: Put each row on a NEW LINE.

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
        financial_data = state.get("financial_data", {})

        await self._emit_status("running", 10, f"Analyzing {len(companies)} companies...")

        # Combine all research data (web research + financial intel)
        research_data_parts = []
        for company in companies:
            company_section = f"### {company}\n\n"

            # Add web research data
            if company in profiles:
                company_section += f"**Web Research:**\n{profiles[company].get('analysis', 'No data')}\n\n"

            # Add financial data
            if company in financial_data:
                company_section += f"**Financial Intelligence:**\n{financial_data[company].get('analysis', 'No financial data')}\n\n"

            research_data_parts.append(company_section)

        research_data = "\n\n".join(research_data_parts)

        # Create helper strings for prompt
        company_list = " | ".join(companies)
        separator = "|".join(["---" for _ in companies])

        await self._emit_status("running", 50, "Creating comparative analysis...")

        # Get comparison angles from coordinator for focused analysis
        comparison_angles = state.get("comparison_angles", [])
        if comparison_angles:
            angles_guidance = f"\n\nPRIORITY COMPARISON DIMENSIONS (from coordinator):\n" + "\n".join(f"- {angle}" for angle in comparison_angles)
            research_data_enhanced = research_data + angles_guidance
            print(f"[i] Using coordinator's comparison angles: {comparison_angles}")
        else:
            research_data_enhanced = research_data
            print(f"[i] Using default analysis (no coordinator angles)")

        # Get depth setting from coordinator to adjust analysis scope
        depth_settings = state.get("depth_settings", {})
        analysis_depth = state.get("analysis_depth", "standard")

        # Add depth instructions to guide LLM
        if analysis_depth == "light":
            depth_instruction = "\n\nANALYSIS DEPTH: Light - Focus on Feature Comparison Matrix only. Skip SWOT and detailed positioning."
        elif analysis_depth == "comprehensive":
            depth_instruction = "\n\nANALYSIS DEPTH: Comprehensive - Include detailed SWOT, market positioning, competitive dynamics, and strategic recommendations."
        else:
            depth_instruction = "\n\nANALYSIS DEPTH: Standard - Include Feature Matrix, SWOT, and Market Positioning."

        research_data_enhanced += depth_instruction
        print(f"[i] Analysis depth: {analysis_depth}")

        # Generate analysis with LLM
        messages = self.analysis_prompt.format_messages(
            companies=", ".join(companies),
            research_data=research_data_enhanced,
            company_list=company_list,
            separator=separator
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
