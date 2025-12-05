"""Content Synthesizer Agent - Generates final research report."""

from typing import Dict, Any
from langchain_core.language_models import BaseLLM
from langchain_core.prompts import ChatPromptTemplate
from .base import BaseAgent
from .state import MarketResearchState
from ..core.tokens import truncate_to_token_limit


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

Use clear, professional language suitable for decision-makers.

CRITICAL: Do NOT include "Executive Summary" as a header. Just write the content directly since the UI already has the header.

Use markdown formatting:
- Use **bold** for emphasis
- Use bullet points with * for lists
- Use clear paragraphs"""),
            ("human", """Query: {query}

Comparative Analysis:
{analysis}

Write an executive summary. Do NOT start with "Executive Summary:" or any header. Just write the summary content with proper markdown formatting.""")
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

        # Get research objectives from coordinator for report structure
        research_objectives = state.get("research_objectives", [])
        if research_objectives:
            objectives_text = "\n\nKEY RESEARCH OBJECTIVES TO ADDRESS:\n" + "\n".join(f"{i+1}. {obj}" for i, obj in enumerate(research_objectives))
            print(f"[i] Structuring report around {len(research_objectives)} objectives from coordinator")
        else:
            objectives_text = ""
            print(f"[i] No research objectives from coordinator, using default structure")

        await self._emit_status("running", 10, "Synthesizing research...")

        # Combine research findings
        research_text = "\n\n".join([
            f"### {company}\n{profile.get('analysis', '')}"
            for company, profile in profiles.items()
        ])

        # Generate executive summary
        await self._emit_status("running", 30, "Writing executive summary...")

        # Truncate analysis to fit in context window (leave room for prompt + response)
        # Reserve ~2000 tokens for prompt template + 1000 for response = 3000 total
        # Context window: 8192 tokens, so 5000 for analysis is safe
        analysis_with_objectives = analysis + objectives_text
        analysis_truncated = truncate_to_token_limit(
            analysis_with_objectives,
            max_tokens=5000,
            model_name=self._get_model_name(),
            suffix="... (truncated for length)"
        )

        summary_messages = self.summary_prompt.format_messages(
            query=query,
            analysis=analysis_truncated
        )
        summary_response = await self.llm.ainvoke(summary_messages)
        executive_summary = summary_response.content if hasattr(summary_response, 'content') else str(summary_response)

        # Track cost for executive summary generation
        summary_cost = self._track_cost(analysis_truncated, executive_summary)

        # Generate full report
        await self._emit_status("running", 60, "Writing detailed report...")

        # Truncate research text to fit context (research can be very long with multiple companies)
        # Include objectives to guide report structure
        research_with_objectives = research_text + objectives_text
        research_truncated = truncate_to_token_limit(
            research_with_objectives,
            max_tokens=4000,
            model_name=self._get_model_name(),
            suffix="... (additional research truncated for length)"
        )

        # Truncate analysis for report too (prevent context overflow)
        analysis_for_report = truncate_to_token_limit(
            analysis,
            max_tokens=3000,
            model_name=self._get_model_name(),
            suffix="... (analysis truncated)"
        )

        report_messages = self.report_prompt.format_messages(
            query=query,
            companies=", ".join(companies),
            research=research_truncated,
            analysis=analysis_for_report
        )
        report_response = await self.llm.ainvoke(report_messages)
        final_report = report_response.content if hasattr(report_response, 'content') else str(report_response)

        # Track cost for full report generation
        report_input = research_truncated + analysis_for_report
        report_cost = self._track_cost(report_input, final_report)

        await self._emit_status("running", 90, "Finalizing report...")

        # Aggregate costs from both LLM calls (summary + report)
        total_input_tokens = summary_cost.get("input_tokens", 0) + report_cost.get("input_tokens", 0)
        total_output_tokens = summary_cost.get("output_tokens", 0) + report_cost.get("output_tokens", 0)
        total_cost = summary_cost.get("estimated_cost_usd", 0.0) + report_cost.get("estimated_cost_usd", 0.0)

        cost_info = {
            "agent": self.name,
            "input_tokens": total_input_tokens,
            "output_tokens": total_output_tokens,
            "total_tokens": total_input_tokens + total_output_tokens,
            "estimated_cost_usd": total_cost,
            "model_name": self._get_model_name(),
            "timestamp": summary_cost.get("timestamp", 0),
            "llm_calls": 2,  # Summary + Report
            "summary_tokens": summary_cost.get("total_tokens", 0),
            "report_tokens": report_cost.get("total_tokens", 0)
        }

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
