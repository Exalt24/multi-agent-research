"""Coordinator Agent - Orchestrates the workflow."""

from typing import Dict, Any
from langchain_core.language_models import BaseLLM
from langchain_core.prompts import ChatPromptTemplate
from .base import BaseAgent
from .state import MarketResearchState


class CoordinatorAgent(BaseAgent):
    """Agent that coordinates the research workflow.

    Responsibilities:
    - Plans research strategy
    - Decides agent execution order
    - Handles errors and retries
    - Manages HITL approvals (future)
    - Provides workflow status updates
    """

    def __init__(self, llm: BaseLLM, **kwargs):
        super().__init__(
            name="Coordinator Agent",
            llm=llm,
            **kwargs
        )

        # Prompt for planning
        self.planning_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a research coordinator planning a market research workflow.

Based on the query, determine:
1. Which agents are needed
2. Execution order (parallel or sequential)
3. Special considerations
4. Estimated complexity (basic/standard/comprehensive)

Output a brief plan."""),
            ("human", """Query: {query}
Companies: {companies}
Requested depth: {analysis_depth}

Create a research plan.""")
        ])

    async def _process(self, state: MarketResearchState) -> Dict[str, Any]:
        """Plan and coordinate the workflow.

        Args:
            state: Current workflow state

        Returns:
            State updates with plan
        """
        query = state.get("query", "")
        companies = state.get("companies", [])
        depth = state.get("analysis_depth", "standard")

        await self._emit_status("running", 20, "Planning research workflow...")

        # Create plan with LLM
        messages = self.planning_prompt.format_messages(
            query=query,
            companies=", ".join(companies),
            analysis_depth=depth
        )

        response = await self.llm.ainvoke(messages)
        plan = response.content if hasattr(response, 'content') else str(response)

        await self._emit_status("running", 80, "Workflow planned")

        # Track cost
        cost_info = self._track_cost(query, plan)

        # For now, return simple coordination
        # In full implementation, this would route to different agents
        return {
            "current_agent": self.name,
            "current_phase": "planning",
            "workflow_status": "running",
            "cost_tracking": {
                **state.get("cost_tracking", {}),
                self.name: cost_info
            }
        }
