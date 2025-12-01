"""Pydantic schemas for API requests/responses."""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class ResearchRequest(BaseModel):
    """Request to start research."""

    query: str = Field(..., description="Research query", min_length=1)
    companies: List[str] = Field(..., description="Companies to research", min_items=1)
    analysis_depth: str = Field("standard", description="Analysis depth: basic, standard, comprehensive")


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
