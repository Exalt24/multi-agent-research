"""State schema for multi-agent market research workflow."""

import operator
from typing import Annotated, List, Dict, Any
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage


class MarketResearchState(TypedDict):
    """State for the market research workflow.

    This state is passed between all agents in the LangGraph workflow.
    Uses Annotated with operator.add for accumulating lists across agents.
    """

    # Core workflow tracking
    messages: Annotated[List[BaseMessage], operator.add]
    current_phase: str  # "research", "analysis", "synthesis", "complete"
    current_agent: str
    workflow_status: str  # "running", "waiting_approval", "completed", "failed"

    # Input
    query: str
    companies: List[str]
    analysis_depth: str  # "basic", "standard", "comprehensive"

    # Research findings (accumulated from research agents)
    research_findings: Annotated[List[Dict[str, Any]], operator.add]
    competitor_profiles: Dict[str, Dict[str, Any]]  # company name -> profile data
    financial_data: Dict[str, Dict[str, Any]]  # company name -> financial info

    # Analysis outputs
    comparative_analysis: Dict[str, Any]  # feature matrix, pricing analysis, etc.
    fact_check_results: Annotated[List[Dict[str, Any]], operator.add]
    validated_claims: List[Dict[str, Any]]

    # Synthesis outputs
    visualizations: List[Dict[str, Any]]  # chart specifications
    final_report: str  # markdown report
    executive_summary: str

    # Metadata and tracking
    session_id: str
    started_at: str
    completed_at: str
    errors: Annotated[List[Dict[str, Any]], operator.add]
    cost_tracking: Dict[str, Any]  # tokens used, estimated cost

    # Human-in-the-Loop
    pending_approvals: List[Dict[str, Any]]
    approval_responses: Dict[str, bool]  # approval_id -> approved
