"""State schema for multi-agent market research workflow.

STATE DESIGN PRINCIPLES:
========================

1. operator.add for Parallel-Safe Lists:
   Fields with operator.add automatically concatenate when multiple agents
   write to them in parallel. Critical for parallel execution!

2. Unique Keys for Parallel Agents:
   Agents writing in parallel use different top-level keys to avoid conflicts.
   Example: web_research → competitor_profiles, financial_intel → financial_data

3. TypedDict for LangGraph:
   LangGraph requires dict-like state for native integration and serialization.

4. String Timestamps:
   ISO 8601 strings for JSON compatibility (WebSocket, API responses).
   Use utility functions for datetime operations.

5. Literal Types:
   Use Literal for string enums to get type safety without enum overhead.
"""

import operator
from typing import Annotated, List, Dict, Any, Literal
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage

# Type aliases for better readability and type safety
WorkflowPhase = Literal["planning", "research", "analysis", "synthesis", "complete"]
WorkflowStatus = Literal["running", "waiting_approval", "completed", "failed"]
AnalysisDepth = Literal["basic", "standard", "comprehensive"]
AgentStatus = Literal["pending", "running", "completed", "failed", "retrying"]


class MarketResearchState(TypedDict):
    """State for the market research workflow.

    This state is passed between all agents in the LangGraph workflow.
    Uses Annotated with operator.add for accumulating lists across parallel agents.

    PARALLEL EXECUTION SAFETY:
    - Fields with operator.add concatenate when agents run in parallel
    - Fields without operator.add use last-write-wins (safe if different agents write to different keys)
    """

    # Core workflow tracking
    messages: Annotated[List[BaseMessage], operator.add]
    current_phase: WorkflowPhase
    current_agent: Annotated[List[str], operator.add]  # List of active agents (supports parallel execution)
    workflow_status: WorkflowStatus

    # Input
    query: str
    companies: List[str]
    analysis_depth: AnalysisDepth

    # Coordination and Strategic Guidance
    research_plan: str  # Coordinator's research strategy (markdown for users)
    research_objectives: List[str]  # Key questions to answer
    search_priorities: Dict[str, List[str]]  # company -> priority keywords/topics
    financial_priorities: List[str]  # Key financial metrics to collect
    comparison_angles: List[str]  # Dimensions for competitive comparison
    depth_settings: Dict[str, str]  # Agent-specific depth settings (light/standard/comprehensive)

    # Research findings (accumulated from research agents)
    research_findings: Annotated[List[Dict[str, Any]], operator.add]
    competitor_profiles: Dict[str, Dict[str, Any]]  # company name -> profile data
    financial_data: Dict[str, Dict[str, Any]]  # company name -> financial info

    # Analysis outputs
    comparative_analysis: Dict[str, Any]  # feature matrix, pricing analysis, etc.
    fact_check_results: Annotated[List[Dict[str, Any]], operator.add]
    validated_claims: List[Dict[str, Any]]

    # Synthesis outputs
    visualizations: Annotated[List[Dict[str, Any]], operator.add]  # chart specs (operator.add for future parallel viz generation)
    final_report: str  # markdown report
    executive_summary: str

    # Metadata and tracking
    session_id: str
    started_at: str
    completed_at: str
    errors: Annotated[List[Dict[str, Any]], operator.add]
    cost_tracking: Dict[str, Any]  # tokens used, estimated cost

    # Human-in-the-Loop (HITL) - IMPLEMENTED
    # Workflow can pause for human approval when quality concerns detected.
    # Currently used by: Fact Checker Agent (pauses if unverified claims found)
    # Use cases: High-stakes decisions, low-confidence results, regulatory compliance
    # Example: Fact checker finds issues → pause → modal appears → user decides → workflow resumes/stops
    pending_approvals: List[Dict[str, Any]]  # Approval requests waiting for human input
    approval_responses: Dict[str, bool]  # approval_id -> approved (True/False)
