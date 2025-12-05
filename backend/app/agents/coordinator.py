"""Coordinator Agent - Orchestrates the workflow."""

from typing import Dict, Any
import json
from langchain_core.language_models import BaseLLM
from langchain_core.prompts import ChatPromptTemplate
from .base import BaseAgent
from .state import MarketResearchState


class CoordinatorAgent(BaseAgent):
    """Agent that coordinates the research workflow.

    Responsibilities:
    - Creates strategic research plan with focus areas and success criteria
    - Identifies key metrics and data points to prioritize
    - Provides context and guidance for downstream agents
    - Sets workflow expectations visible to users

    Note:
    - Agent execution order is defined in graph.py (parallel execution)
    - This agent provides strategic direction, not dynamic routing
    - Research plan is stored in state and used by other agents for context
    """

    def __init__(self, llm: BaseLLM, **kwargs):
        super().__init__(name="Coordinator Agent", llm=llm, **kwargs)

        # Prompt for strategic planning with structured output
        self.planning_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are a strategic research coordinator for competitive intelligence.

Your job is to create actionable guidance that downstream AI agents will use.

Analyze the query and output JSON with this EXACT structure:

```json
{{
  "research_objectives": [
    "Specific question 1",
    "Specific question 2",
    "Specific question 3"
  ],
  "search_priorities": {{
    "Company1": ["keyword1", "keyword2", "keyword3"],
    "Company2": ["keyword1", "keyword2", "keyword3"]
  }},
  "financial_priorities": [
    "revenue_growth",
    "funding_rounds",
    "valuation"
  ],
  "comparison_angles": [
    "feature_parity",
    "pricing_strategy",
    "target_market"
  ],
  "depth_settings": {{
    "web_research": "comprehensive",
    "financial_intel": "standard",
    "data_viz": "standard"
  }},
  "user_plan": "## Research Strategy\\n\\n### Objectives\\n- Find pricing...\\n\\n### Approach\\n- Focus on..."
}}
```

Guidelines:
- research_objectives: 3-5 specific questions the research must answer
- search_priorities: For each company, list 3-5 keywords/topics to prioritize in web search
- financial_priorities: List 3-5 key financial metrics to collect (revenue, funding, valuation, growth_rate, etc.)
- comparison_angles: List 3-5 dimensions for comparing companies (features, pricing, performance, etc.)
- depth_settings: Set depth for each agent type: "light", "standard", or "comprehensive"
- user_plan: Markdown-formatted strategy for users to read (include objectives, approach, focus areas)

Be specific and actionable. Think like a research director giving clear instructions to analysts.""",
                ),
                (
                    "human",
                    """Query: {query}
Companies: {companies}
Analysis Depth: {analysis_depth}

Generate the strategic research guidance in JSON format.""",
                ),
            ]
        )

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
            query=query, companies=", ".join(companies), analysis_depth=depth
        )

        response = await self.llm.ainvoke(messages)
        raw_response = response.content if hasattr(response, "content") else str(response)

        await self._emit_status("running", 60, "Parsing strategic guidance...")

        # Parse JSON from LLM response
        try:
            # Extract JSON from markdown code blocks if present
            if "```json" in raw_response:
                json_str = raw_response.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_response:
                json_str = raw_response.split("```")[1].split("```")[0].strip()
            else:
                json_str = raw_response

            guidance = json.loads(json_str)

            # Extract components
            research_objectives = guidance.get("research_objectives", [])
            search_priorities = guidance.get("search_priorities", {})
            financial_priorities = guidance.get("financial_priorities", [])
            comparison_angles = guidance.get("comparison_angles", [])
            depth_settings = guidance.get("depth_settings", {})
            user_plan = guidance.get("user_plan", "")

        except (json.JSONDecodeError, ValueError, IndexError) as e:
            print(f"[!] Failed to parse coordinator JSON: {e}")
            print(f"[!] LLM response: {raw_response[:300]}...")

            # Fallback: Use basic defaults based on query
            research_objectives = [
                f"Understand {query}",
                "Compare competitive positioning",
                "Identify market opportunities"
            ]
            search_priorities = {company: ["overview", "features", "pricing"] for company in companies}
            financial_priorities = ["funding", "revenue", "growth"]
            comparison_angles = ["features", "pricing", "market_position"]
            depth_settings = {"web_research": depth, "financial_intel": depth, "data_viz": "standard"}
            user_plan = f"## Research Strategy\n\n### Query\n{query}\n\n### Companies\n{', '.join(companies)}\n\n### Approach\nComprehensive competitive analysis."

        await self._emit_status("running", 90, "Strategic guidance ready")

        # Track cost
        cost_info = self._track_cost(str(messages), raw_response)

        # Return strategic guidance that all downstream agents can use
        return {
            "research_plan": user_plan,
            "research_objectives": research_objectives,
            "search_priorities": search_priorities,
            "financial_priorities": financial_priorities,
            "comparison_angles": comparison_angles,
            "depth_settings": depth_settings,
            "current_agent": [self.name],  # List for operator.add
            "current_phase": "research",  # Move to research phase
            "workflow_status": "running",
            "cost_tracking": {**state.get("cost_tracking", {}), self.name: cost_info},
        }
