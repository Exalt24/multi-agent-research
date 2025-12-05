"""Fact Checker Agent - Validates claims and checks sources."""

from typing import Dict, Any, List
from langchain_core.language_models import BaseLLM
from langchain_core.prompts import ChatPromptTemplate
from .base import BaseAgent
from .state import MarketResearchState
from .tools.search import SearchManager
from ..core.tokens import truncate_to_token_limit


class FactCheckerAgent(BaseAgent):
    """Agent that validates claims and verifies information.

    Checks:
    - Factual accuracy of claims
    - Source reliability
    - Contradictions in data
    - Confidence scores per claim
    """

    def __init__(self, llm: BaseLLM, tavily_api_key: str = None, **kwargs):
        super().__init__(
            name="Fact Checker Agent",
            llm=llm,
            **kwargs
        )
        self.search_manager = SearchManager(tavily_api_key)

        # Prompt for fact checking
        self.fact_check_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a fact-checker verifying research claims.

CRITICAL: Output MUST be in clean markdown format with proper structure.

For each major claim in the analysis:
1. Identify the claim
2. Assess confidence (High/Medium/Low) based on sources
3. Flag contradictions or unsupported statements
4. Note if verification needed

FORMATTING RULES:
- Use ## for main sections (H2)
- Use - for bullet lists with proper format
- Add blank lines between sections
- Use **bold** for confidence levels
- Keep structured and clear"""),
            ("human", """Analysis to verify:
{analysis}

Fact-check this analysis using this EXACT format:

## Verified Claims

- **Claim:** [Exact claim from analysis]
  **Confidence:** High/Medium/Low
  **Reasoning:** [Why this confidence level based on sources]

(Repeat for 3-5 major claims)

## Flagged for Review

- **Claim:** [Claim that needs verification]
  **Issue:** [Contradiction, unsupported, or needs more data]

(List any problematic claims, or "No major issues found")

## Overall Assessment

[2-3 sentences summarizing the data quality, source reliability, and overall confidence in the analysis]

Follow this structure exactly with proper markdown formatting.""")
        ])

    async def _process(self, state: MarketResearchState) -> Dict[str, Any]:
        """Fact-check the analysis.

        Args:
            state: Current workflow state

        Returns:
            State updates with fact-check results
        """
        analysis = state.get("comparative_analysis", {}).get("analysis_text", "")

        await self._emit_status("running", 10, "Fact-checking analysis...")

        # Truncate analysis to fit context window (use actual model for accurate truncation)
        analysis_truncated = truncate_to_token_limit(
            analysis,
            max_tokens=5000,
            model_name=self._get_model_name(),
            suffix="... (analysis truncated for length)"
        )

        # Fact-check with LLM
        messages = self.fact_check_prompt.format_messages(
            analysis=analysis_truncated
        )

        response = await self.llm.ainvoke(messages)
        fact_check_report = response.content if hasattr(response, 'content') else str(response)

        await self._emit_status("running", 80, "Finalizing fact-check...")

        # Track cost
        cost_info = self._track_cost(analysis, fact_check_report)

        # Structure results
        fact_check_result = {
            "report": fact_check_report,
            "timestamp": cost_info["timestamp"],
            "agent": self.name
        }

        # HITL Gate: Check if approval needed for low-confidence results
        # If fact-check report contains warnings or failed claims, ask user
        report_lower = fact_check_report.lower()
        needs_approval = (
            "unverified" in report_lower or
            "could not verify" in report_lower or
            "insufficient evidence" in report_lower or
            "contradictory" in report_lower
        )

        if needs_approval:
            await self._emit_status("running", 85, "Quality concerns detected, requesting human review...")

            try:
                # Request human approval
                approval_response = await self._request_approval(
                    approval_id=f"fact-check-{state.get('session_id', 'unknown')[:8]}",
                    question="Fact-check found potential issues. Review the report and decide whether to continue.",
                    context={
                        "report_preview": fact_check_report[:500] + "...",
                        "concerns": "Unverified claims or insufficient evidence detected"
                    },
                    options=["Continue Anyway", "Stop Workflow"],
                    timeout=300  # 5 minutes
                )

                # Check user decision
                if approval_response["decision"] == "reject" or "Stop" in approval_response.get("decision", ""):
                    # User chose to stop - add error to halt workflow
                    return {
                        "fact_check_results": [fact_check_result],
                        "validated_claims": [],
                        "current_agent": self.name,
                        "current_phase": "validation",
                        "workflow_status": "failed",
                        "errors": [{
                            "agent": self.name,
                            "error": "Workflow stopped by user after fact-check review",
                            "timestamp": cost_info["timestamp"]
                        }],
                        "cost_tracking": {
                            **state.get("cost_tracking", {}),
                            self.name: cost_info
                        }
                    }

                # User approved - continue with workflow
                await self._emit_status("running", 90, "Human approval received, continuing...")

            except TimeoutError:
                # Timeout - default to continuing (don't block workflow forever)
                await self._emit_status("running", 90, "Approval timeout - continuing with workflow...")
            except Exception as e:
                # HITL error - log but continue (don't break workflow on HITL failures)
                print(f"[!] HITL approval failed: {e}")
                await self._emit_status("running", 90, "Approval failed - continuing with workflow...")

        return {
            "fact_check_results": [fact_check_result],
            "validated_claims": [],  # Could parse report into structured claims
            "current_agent": self.name,
            "current_phase": "validation",
            "cost_tracking": {
                **state.get("cost_tracking", {}),
                self.name: cost_info
            }
        }
