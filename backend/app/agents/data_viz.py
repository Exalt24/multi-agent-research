"""Data Visualization Agent - Generates chart specifications."""

from typing import Dict, Any, List
from langchain_core.language_models import BaseLLM
from langchain_core.prompts import ChatPromptTemplate
from .base import BaseAgent
from .state import MarketResearchState
import json


class DataVisualizationAgent(BaseAgent):
    """Agent that generates visualization specifications.

    Creates:
    - Chart.js configurations for frontend rendering
    - Recommendations for best chart types
    - Data formatted for visualization
    """

    def __init__(self, llm: BaseLLM, **kwargs):
        super().__init__(
            name="Data Visualization Agent",
            llm=llm,
            **kwargs
        )

        # Prompt for chart recommendations
        self.viz_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a data visualization expert.

Recommend charts for the research data. For each recommendation:
1. Chart type (bar, line, radar, scatter, etc.)
2. What it shows
3. Why it's useful
4. Data structure needed

Output as JSON array:
[
  {{
    "title": "Chart title",
    "type": "bar|line|radar|scatter|pie",
    "description": "What it shows",
    "reason": "Why useful",
    "data_keys": ["key1", "key2"]
  }}
]"""),
            ("human", """Companies: {companies}

Comparative Analysis:
{analysis}

Recommend 3-5 visualizations for this research report.""")
        ])

    async def _process(self, state: MarketResearchState) -> Dict[str, Any]:
        """Generate visualization recommendations.

        Args:
            state: Current workflow state

        Returns:
            State updates with chart specs
        """
        companies = state.get("companies", [])
        analysis = state.get("comparative_analysis", {}).get("analysis_text", "")

        await self._emit_status("running", 20, "Recommending visualizations...")

        # Get recommendations from LLM
        messages = self.viz_prompt.format_messages(
            companies=", ".join(companies),
            analysis=analysis[:2000]  # Limit for token management
        )

        response = await self.llm.ainvoke(messages)
        recommendations = response.content if hasattr(response, 'content') else str(response)

        await self._emit_status("running", 60, "Creating chart specifications...")

        # Try to parse JSON, fallback to default charts if parsing fails
        try:
            # Extract JSON from markdown code blocks if present
            if "```json" in recommendations:
                json_str = recommendations.split("```json")[1].split("```")[0].strip()
            elif "```" in recommendations:
                json_str = recommendations.split("```")[1].split("```")[0].strip()
            else:
                json_str = recommendations

            chart_specs = json.loads(json_str)
        except:
            # Fallback: default charts
            chart_specs = [
                {
                    "title": "Feature Comparison",
                    "type": "radar",
                    "description": "Compare features across companies",
                    "reason": "Shows multi-dimensional comparison",
                    "data_keys": companies
                },
                {
                    "title": "Market Positioning",
                    "type": "scatter",
                    "description": "Position companies on price vs features",
                    "reason": "Visual market positioning",
                    "data_keys": ["price", "features"]
                }
            ]

        # Add visualization specs to state
        visualizations = [
            {
                **spec,
                "agent": self.name,
                "companies": companies
            }
            for spec in chart_specs[:5]  # Limit to 5 charts
        ]

        await self._emit_status("running", 90, "Finalizing visualizations...")

        # Track cost
        cost_info = self._track_cost(analysis, recommendations)

        return {
            "visualizations": visualizations,
            "current_agent": self.name,
            "current_phase": "visualization",
            "cost_tracking": {
                **state.get("cost_tracking", {}),
                self.name: cost_info
            }
        }
