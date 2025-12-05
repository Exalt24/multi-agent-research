"""Data Visualization Agent - Generates chart specifications."""

from typing import Dict, Any, List
from langchain_core.language_models import BaseLLM
from langchain_core.prompts import ChatPromptTemplate
from .base import BaseAgent
from .state import MarketResearchState
from ..core.tokens import truncate_to_token_limit
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
1. Chart type (MUST be: bar, line, pie, or doughnut - these are rendered by frontend)
2. What it shows
3. Why it's useful
4. Chart.js data structure

SUPPORTED CHART TYPES (frontend ChartRenderer supports these):
- **bar**: Side-by-side comparisons (features, metrics, scores)
- **line**: Trends, growth, progression
- **pie**: Distribution, market share, percentages
- **doughnut**: Similar to pie with center space

Output as JSON array with Chart.js data format:
[
  {{
    "title": "Chart title",
    "type": "bar|line|pie|doughnut",
    "description": "What it shows",
    "reason": "Why useful",
    "data": {{
      "labels": ["Company A", "Company B"],
      "datasets": [{{
        "label": "Metric name",
        "data": [85, 92],
        "backgroundColor": ["#0ea5e9", "#8b5cf6"]
      }}]
    }}
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

        # Truncate analysis to fit context window (use actual model for accurate truncation)
        analysis_truncated = truncate_to_token_limit(
            analysis,
            max_tokens=3000,
            model_name=self._get_model_name(),
            suffix="... (analysis truncated for length)"
        )

        # Get recommendations from LLM
        messages = self.viz_prompt.format_messages(
            companies=", ".join(companies),
            analysis=analysis_truncated
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
        except (json.JSONDecodeError, ValueError, IndexError) as e:
            print(f"[!] Failed to parse chart specs from LLM: {e}")
            print(f"[!] LLM response was: {recommendations[:200]}...")
            # Fallback: default charts (using types supported by frontend ChartRenderer)
            chart_specs = [
                {
                    "title": "Company Comparison",
                    "type": "bar",
                    "description": "Compare key metrics across companies",
                    "reason": "Shows clear side-by-side comparison",
                    "data": {
                        "labels": companies,
                        "datasets": [{
                            "label": "Overall Score",
                            "data": [85, 88, 75],
                            "backgroundColor": ["#0ea5e9", "#8b5cf6", "#f97316"]
                        }]
                    }
                },
                {
                    "title": "Market Distribution",
                    "type": "pie",
                    "description": "Market share distribution",
                    "reason": "Visual market positioning",
                    "data": {
                        "labels": companies,
                        "datasets": [{
                            "label": "Market Share",
                            "data": [45, 35, 20],
                            "backgroundColor": ["#0ea5e9", "#8b5cf6", "#f97316"]
                        }]
                    }
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
            "current_agent": [self.name],  # List for operator.add (parallel-safe)
            # Don't update current_phase (Content Synthesizer sets it, both agents in same phase)
            "cost_tracking": {
                **state.get("cost_tracking", {}),
                self.name: cost_info
            }
        }
