"""LangGraph workflow definition."""

from typing import List, Dict
from langgraph.graph import StateGraph, END
from .state import MarketResearchState
from .web_research import WebResearchAgent
from ..core.llm import get_llm
from ..core.config import get_settings
import uuid
from datetime import datetime

settings = get_settings()


def create_research_graph():
    """Create the research workflow graph.

    For now, this is a minimal version with just Web Research Agent.
    Will expand to full 7-agent system later.
    """

    # Initialize agents
    llm = get_llm(temperature=0.7)

    web_research_agent = WebResearchAgent(
        llm=llm,
        tavily_api_key=settings.tavily_api_key,
        rag_api_url=settings.rag_api_url
    )

    # Define workflow graph
    workflow = StateGraph(MarketResearchState)

    # Add nodes
    workflow.add_node("web_research", web_research_agent.execute)

    # Define edges
    workflow.set_entry_point("web_research")
    workflow.add_edge("web_research", END)

    return workflow.compile()


async def run_research(
    query: str,
    companies: List[str],
    analysis_depth: str = "standard"
) -> Dict:
    """Run research workflow.

    Args:
        query: Research query
        companies: List of companies to research
        analysis_depth: Depth of analysis

    Returns:
        Final state
    """
    # Initialize state
    initial_state: MarketResearchState = {
        "messages": [],
        "current_phase": "research",
        "current_agent": "",
        "workflow_status": "running",
        "query": query,
        "companies": companies,
        "analysis_depth": analysis_depth,
        "research_findings": [],
        "competitor_profiles": {},
        "financial_data": {},
        "comparative_analysis": {},
        "fact_check_results": [],
        "validated_claims": [],
        "visualizations": [],
        "final_report": "",
        "executive_summary": "",
        "session_id": str(uuid.uuid4()),
        "started_at": datetime.utcnow().isoformat(),
        "completed_at": "",
        "errors": [],
        "cost_tracking": {},
        "pending_approvals": [],
        "approval_responses": {}
    }

    # Create and run graph
    graph = create_research_graph()
    final_state = await graph.ainvoke(initial_state)

    return final_state
