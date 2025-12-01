"""LangGraph workflow definition - Complete 7-agent system."""

from typing import List, Dict
from langgraph.graph import StateGraph, END, START
from .state import MarketResearchState
from .coordinator import CoordinatorAgent
from .web_research import WebResearchAgent
from .financial_intel import FinancialIntelligenceAgent
from .data_analyst import DataAnalystAgent
from .fact_checker import FactCheckerAgent
from .content_synthesizer import ContentSynthesizerAgent
from .data_viz import DataVisualizationAgent
from ..core.llm import get_llm
from ..core.config import get_settings
import uuid
from datetime import datetime

settings = get_settings()


def create_research_graph():
    """Create the complete research workflow graph.

    Workflow:
    1. Coordinator (plans workflow)
    2. Web Research + Financial Intel (parallel research)
    3. Data Analyst (analyzes research)
    4. Fact Checker (validates analysis)
    5. Content Synthesizer + Data Viz (parallel outputs)
    """

    # Initialize all agents
    llm = get_llm(temperature=0.7)

    coordinator = CoordinatorAgent(llm=llm)

    web_research = WebResearchAgent(
        llm=llm,
        tavily_api_key=settings.tavily_api_key,
        rag_api_url=settings.rag_api_url
    )

    financial_intel = FinancialIntelligenceAgent(
        llm=llm,
        tavily_api_key=settings.tavily_api_key
    )

    data_analyst = DataAnalystAgent(llm=llm)

    fact_checker = FactCheckerAgent(
        llm=llm,
        tavily_api_key=settings.tavily_api_key
    )

    content_synthesizer = ContentSynthesizerAgent(llm=llm)

    data_viz = DataVisualizationAgent(llm=llm)

    # Define workflow graph
    workflow = StateGraph(MarketResearchState)

    # Add all agent nodes
    workflow.add_node("coordinator", coordinator.execute)
    workflow.add_node("web_research", web_research.execute)
    workflow.add_node("financial_intel", financial_intel.execute)
    workflow.add_node("data_analyst", data_analyst.execute)
    workflow.add_node("fact_checker", fact_checker.execute)
    workflow.add_node("content_synthesizer", content_synthesizer.execute)
    workflow.add_node("data_viz", data_viz.execute)

    # Define workflow edges - Sequential for now (parallel can be complex in LangGraph)
    # Start → Coordinator
    workflow.set_entry_point("coordinator")

    # Coordinator → Web Research (sequential)
    workflow.add_edge("coordinator", "web_research")

    # Web Research → Financial Intel
    workflow.add_edge("web_research", "financial_intel")

    # Financial Intel → Data Analyst
    workflow.add_edge("financial_intel", "data_analyst")

    # Data Analyst → Fact Checker
    workflow.add_edge("data_analyst", "fact_checker")

    # Fact Checker → Content Synthesizer
    workflow.add_edge("fact_checker", "content_synthesizer")

    # Content Synthesizer → Data Viz
    workflow.add_edge("content_synthesizer", "data_viz")

    # Data Viz → END
    workflow.add_edge("data_viz", END)

    return workflow.compile()


async def run_research(
    query: str,
    companies: List[str],
    analysis_depth: str = "standard"
) -> Dict:
    """Run complete research workflow with all 7 agents.

    Args:
        query: Research query
        companies: List of companies to research
        analysis_depth: Depth of analysis

    Returns:
        Final state with complete research report
    """
    # Initialize state
    initial_state: MarketResearchState = {
        "messages": [],
        "current_phase": "planning",
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

    # Create and run complete graph
    graph = create_research_graph()
    final_state = await graph.ainvoke(initial_state)

    # Mark completion
    final_state["completed_at"] = datetime.utcnow().isoformat()
    final_state["workflow_status"] = "completed"

    return final_state
