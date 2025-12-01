"""Content Synthesizer Agent - Generates final research report."""

from typing import Dict, Any
from langchain_core.language_models import BaseLLM
from langchain_core.prompts import ChatPromptTemplate
from .base import BaseAgent
from .state import MarketResearchState


class ContentSynthesizerAgent(BaseAgent):
    """Agent that synthesizes all research into a final report.

    Produces:
    - Executive summary
    - Detailed research report in markdown
    - Key findings and recommendations
    """

    def __init__(self, llm: BaseLLM, **kwargs):
        super().__init__(
            name="Content Synthesizer Agent",
            llm=llm,
            **kwargs
        )

        # Prompt for executive summary
        self.summary_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a business analyst writing executive summaries.

Create a concise executive summary (2-3 paragraphs) that captures:
1. Research objective
2. Key findings
3. Main competitive differences
4. Recommendation (if applicable)

Use clear, professional language suitable for decision-makers."""),
            ("human", """Query: {query}

Comparative Analysis:
{analysis}

Write an executive summary.""")
        ])

        # Prompt for full report
        self.report_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a research analyst writing comprehensive market research reports.

CRITICAL: Use STRICT markdown formatting. Every section MUST start with proper headers.

Required structure (use these EXACT headers):

# Market Research Report

## Executive Summary
[2-3 paragraphs here]

## Research Methodology
[Brief methodology]

## Competitive Analysis
{analysis}

## Key Findings
- Finding 1
- Finding 2
- Finding 3

## Recommendations
1. Recommendation 1
2. Recommendation 2

## Appendix: Sources
- Source 1
- Source 2

FORMATTING RULES:
- Use ## for main sections (not # or ###)
- Use - for unordered lists
- Use 1. 2. 3. for ordered lists
- Use **bold** for emphasis
- Add blank lines between sections
- Use tables with | for comparisons
- NO nested headers without content"""),
            ("human", """Query: {query}
Companies: {companies}

Research Findings:
{research}

Comparative Analysis:
{analysis}

Create a comprehensive research report following the EXACT structure above.""")
        ])

    async def _process(self, state: MarketResearchState) -> Dict[str, Any]:
        """Synthesize all research into final report.

        Args:
            state: Current workflow state

        Returns:
            State updates with report
        """
        query = state.get("query", "")
        companies = state.get("companies", [])
        analysis = state.get("comparative_analysis", {}).get("analysis_text", "")
        profiles = state.get("competitor_profiles", {})

        await self._emit_status("running", 10, "Synthesizing research...")

        # Combine research findings
        research_text = "\n\n".join([
            f"### {company}\n{profile.get('analysis', '')}"
            for company, profile in profiles.items()
        ])

        # Generate executive summary
        await self._emit_status("running", 30, "Writing executive summary...")

        summary_messages = self.summary_prompt.format_messages(
            query=query,
            analysis=analysis[:2000]  # Limit for summary
        )
        summary_response = await self.llm.ainvoke(summary_messages)
        executive_summary = summary_response.content if hasattr(summary_response, 'content') else str(summary_response)

        # Generate full report
        await self._emit_status("running", 60, "Writing detailed report...")

        report_messages = self.report_prompt.format_messages(
            query=query,
            companies=", ".join(companies),
            research=research_text[:3000],  # Limit to manage tokens
            analysis=analysis
        )
        report_response = await self.llm.ainvoke(report_messages)
        final_report = report_response.content if hasattr(report_response, 'content') else str(report_response)

        await self._emit_status("running", 90, "Finalizing report...")

        # Track cost
        combined_input = research_text + analysis
        combined_output = executive_summary + final_report
        cost_info = self._track_cost(combined_input, combined_output)

        return {
            "executive_summary": executive_summary,
            "final_report": final_report,
            "current_agent": self.name,
            "current_phase": "synthesis",
            "cost_tracking": {
                **state.get("cost_tracking", {}),
                self.name: cost_info
            }
        }
