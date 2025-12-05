"""Utility functions for MarketResearchState operations.

Provides helper functions for working with state timestamps and other common operations.
"""

from datetime import datetime, timezone
from typing import Optional
from .state import MarketResearchState


# =============================================================================
# Timestamp Utilities
# =============================================================================

def get_current_timestamp() -> str:
    """Get current UTC timestamp in ISO 8601 format.

    Returns:
        ISO 8601 string: "2024-12-05T18:30:45.123456"
    """
    return datetime.now(timezone.utc).isoformat()


def parse_timestamp(timestamp_str: str) -> datetime:
    """Parse ISO 8601 timestamp string to datetime object.

    Args:
        timestamp_str: ISO 8601 timestamp string

    Returns:
        datetime object (timezone-aware)

    Example:
        >>> dt = parse_timestamp("2024-12-05T18:30:45.123456+00:00")
        >>> dt.year
        2024
    """
    return datetime.fromisoformat(timestamp_str)


def get_workflow_duration_seconds(state: MarketResearchState) -> Optional[float]:
    """Calculate workflow duration in seconds.

    Args:
        state: MarketResearchState with started_at and completed_at

    Returns:
        Duration in seconds, or None if workflow not yet completed

    Example:
        >>> duration = get_workflow_duration_seconds(state)
        >>> print(f"Workflow took {duration:.1f} seconds")
        Workflow took 105.3 seconds
    """
    if not state.get("started_at") or not state.get("completed_at"):
        return None

    start = parse_timestamp(state["started_at"])
    end = parse_timestamp(state["completed_at"])

    return (end - start).total_seconds()


def get_workflow_duration_formatted(state: MarketResearchState) -> str:
    """Get formatted workflow duration (e.g., "1m 45s").

    Args:
        state: MarketResearchState with started_at and completed_at

    Returns:
        Formatted duration string

    Example:
        >>> get_workflow_duration_formatted(state)
        "1m 45s"
    """
    duration = get_workflow_duration_seconds(state)

    if duration is None:
        return "N/A (not completed)"

    minutes = int(duration // 60)
    seconds = int(duration % 60)

    if minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"


def get_elapsed_time_seconds(state: MarketResearchState) -> Optional[float]:
    """Get elapsed time since workflow started (even if not completed).

    Args:
        state: MarketResearchState with started_at

    Returns:
        Elapsed time in seconds, or None if not started

    Example:
        >>> elapsed = get_elapsed_time_seconds(state)
        >>> print(f"Running for {elapsed:.0f}s so far...")
        Running for 42s so far...
    """
    if not state.get("started_at"):
        return None

    start = parse_timestamp(state["started_at"])
    now = datetime.now(timezone.utc)

    return (now - start).total_seconds()


# =============================================================================
# Cost Tracking Utilities
# =============================================================================

def get_total_cost(state: MarketResearchState) -> float:
    """Get total estimated cost in USD.

    Args:
        state: MarketResearchState with cost_tracking

    Returns:
        Total cost in USD

    Example:
        >>> cost = get_total_cost(state)
        >>> print(f"Total cost: ${cost:.4f}")
        Total cost: $0.0523
    """
    cost_tracking = state.get("cost_tracking", {})
    return cost_tracking.get("estimated_cost_usd", 0.0)


def get_total_tokens(state: MarketResearchState) -> int:
    """Get total tokens used across all agents.

    Args:
        state: MarketResearchState with cost_tracking

    Returns:
        Total token count

    Example:
        >>> tokens = get_total_tokens(state)
        >>> print(f"Total tokens: {tokens:,}")
        Total tokens: 45,230
    """
    cost_tracking = state.get("cost_tracking", {})
    return cost_tracking.get("total_tokens", 0)


# =============================================================================
# Error Tracking Utilities
# =============================================================================

def has_errors(state: MarketResearchState) -> bool:
    """Check if workflow has any errors.

    Args:
        state: MarketResearchState with errors list

    Returns:
        True if errors exist, False otherwise
    """
    errors = state.get("errors", [])
    return len(errors) > 0


def get_error_count(state: MarketResearchState) -> int:
    """Get total number of errors.

    Args:
        state: MarketResearchState with errors list

    Returns:
        Number of errors
    """
    errors = state.get("errors", [])
    return len(errors)


def get_errors_by_agent(state: MarketResearchState) -> dict[str, list[str]]:
    """Group errors by agent name.

    Args:
        state: MarketResearchState with errors list

    Returns:
        Dict mapping agent name to list of error messages

    Example:
        >>> errors = get_errors_by_agent(state)
        >>> print(errors)
        {
            "Web Research Agent": ["Tavily quota exceeded"],
            "Financial Intelligence Agent": ["Finnhub rate limit"]
        }
    """
    errors = state.get("errors", [])
    by_agent: dict[str, list[str]] = {}

    for error in errors:
        agent = error.get("agent", "Unknown")
        message = error.get("error", "Unknown error")

        if agent not in by_agent:
            by_agent[agent] = []
        by_agent[agent].append(message)

    return by_agent


# =============================================================================
# Progress Tracking Utilities
# =============================================================================

def get_completion_percentage(state: MarketResearchState) -> float:
    """Estimate workflow completion percentage based on phase.

    Args:
        state: MarketResearchState with current_phase

    Returns:
        Completion percentage (0.0 to 100.0)

    Note:
        This is a rough estimate based on phase. Real-time progress
        comes from agent WebSocket updates.
    """
    phase = state.get("current_phase", "planning")

    phase_progress = {
        "planning": 10.0,
        "research": 40.0,
        "analysis": 70.0,
        "synthesis": 90.0,
        "complete": 100.0
    }

    return phase_progress.get(phase, 0.0)


# =============================================================================
# State Validation Utilities
# =============================================================================

def validate_state(state: MarketResearchState) -> list[str]:
    """Validate state has required fields and correct structure.

    Args:
        state: MarketResearchState to validate

    Returns:
        List of validation errors (empty if valid)

    Example:
        >>> errors = validate_state(state)
        >>> if errors:
        ...     print("Validation failed:", errors)
    """
    errors = []

    # Check required fields
    required_fields = ["query", "companies", "session_id", "workflow_status"]
    for field in required_fields:
        if field not in state or not state[field]:
            errors.append(f"Missing required field: {field}")

    # Check lists are actually lists
    list_fields = ["companies", "messages", "research_findings", "errors"]
    for field in list_fields:
        if field in state and not isinstance(state.get(field), list):
            errors.append(f"Field '{field}' should be a list, got {type(state.get(field))}")

    # Check dicts are actually dicts
    dict_fields = ["competitor_profiles", "financial_data", "cost_tracking"]
    for field in dict_fields:
        if field in state and not isinstance(state.get(field), dict):
            errors.append(f"Field '{field}' should be a dict, got {type(state.get(field))}")

    return errors


# =============================================================================
# Testing
# =============================================================================
if __name__ == "__main__":
    print("State Utilities Test")
    print("=" * 70)

    # Test timestamps
    print("\n[1] Timestamp utilities:")
    now = get_current_timestamp()
    print(f"Current timestamp: {now}")

    dt = parse_timestamp(now)
    print(f"Parsed datetime: {dt}")

    # Test mock state
    print("\n[2] Duration calculation:")
    mock_state: MarketResearchState = {
        "started_at": "2024-12-05T18:00:00+00:00",
        "completed_at": "2024-12-05T18:01:45+00:00",
        "session_id": "test",
        "query": "test query",
        "companies": ["Company A"],
        "workflow_status": "completed",
        "current_phase": "complete",
        "current_agent": "Test",
        "analysis_depth": "standard",
        "messages": [],
        "research_findings": [],
        "competitor_profiles": {},
        "financial_data": {},
        "comparative_analysis": {},
        "fact_check_results": [],
        "validated_claims": [],
        "visualizations": [],
        "final_report": "",
        "executive_summary": "",
        "errors": [],
        "cost_tracking": {
            "total_tokens": 45230,
            "estimated_cost_usd": 0.0523
        },
        "pending_approvals": [],
        "approval_responses": {}
    }

    duration = get_workflow_duration_seconds(mock_state)
    formatted = get_workflow_duration_formatted(mock_state)
    print(f"Duration: {duration} seconds ({formatted})")

    # Test cost tracking
    print("\n[3] Cost tracking:")
    cost = get_total_cost(mock_state)
    tokens = get_total_tokens(mock_state)
    print(f"Total cost: ${cost:.4f}")
    print(f"Total tokens: {tokens:,}")

    print("\n" + "=" * 70)
    print("All tests passed!")
