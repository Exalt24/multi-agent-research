"""Pydantic schemas for API requests/responses."""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal


class ResearchRequest(BaseModel):
    """Request to start research."""

    query: str = Field(..., description="Research query", min_length=1)
    companies: List[str] = Field(..., description="Companies to research", min_items=1)
    analysis_depth: Literal["basic", "standard", "comprehensive"] = Field(
        "standard",
        description="Analysis depth: basic (quick), standard (balanced), comprehensive (deep)"
    )


class ResearchResponse(BaseModel):
    """Research workflow response."""

    session_id: str
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    message: str


# Human-in-the-Loop (HITL) Schemas

class ApprovalRequest(BaseModel):
    """Request user approval for workflow decision."""

    session_id: str = Field(..., description="Research session ID")
    approval_id: str = Field(..., description="Unique approval request ID")
    agent: str = Field(..., description="Agent requesting approval")
    question: str = Field(..., description="Question to ask user")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    options: List[str] = Field(default=["Approve", "Reject"], description="Available options")


class ApprovalResponse(BaseModel):
    """User response to approval request."""

    session_id: str = Field(..., description="Research session ID")
    approval_id: str = Field(..., description="Approval request ID being responded to")
    decision: Literal["approve", "reject"] = Field(..., description="User decision")
    feedback: Optional[str] = Field(None, description="Optional user feedback")
