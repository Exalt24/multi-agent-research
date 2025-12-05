"""
Human-in-the-Loop (HITL) Manager

Handles approval requests and responses for workflow gates.
Agents can pause and wait for human approval before proceeding.
"""

from typing import Dict, Any, Optional
import asyncio
from datetime import datetime


class HITLManager:
    """Manages pending approval requests and responses."""

    def __init__(self):
        # session_id -> {approval_id -> approval_data}
        self._pending_approvals: Dict[str, Dict[str, Dict[str, Any]]] = {}

        # session_id -> {approval_id -> asyncio.Event}
        self._approval_events: Dict[str, Dict[str, asyncio.Event]] = {}

        # session_id -> {approval_id -> response}
        self._approval_responses: Dict[str, Dict[str, Dict[str, Any]]] = {}

    def create_approval_request(
        self,
        session_id: str,
        approval_id: str,
        agent: str,
        question: str,
        context: Optional[Dict[str, Any]] = None,
        options: list[str] = None
    ) -> Dict[str, Any]:
        """Create a new approval request.

        Args:
            session_id: Research session ID
            approval_id: Unique approval ID
            agent: Agent name requesting approval
            question: Question to ask user
            context: Additional context
            options: Available options (default: ["Approve", "Reject"])

        Returns:
            Approval request data
        """
        if session_id not in self._pending_approvals:
            self._pending_approvals[session_id] = {}
            self._approval_events[session_id] = {}
            self._approval_responses[session_id] = {}

        approval_data = {
            "approval_id": approval_id,
            "agent": agent,
            "question": question,
            "context": context or {},
            "options": options or ["Approve", "Reject"],
            "requested_at": datetime.utcnow().isoformat(),
            "status": "pending"
        }

        self._pending_approvals[session_id][approval_id] = approval_data
        self._approval_events[session_id][approval_id] = asyncio.Event()

        return approval_data

    async def wait_for_approval(
        self,
        session_id: str,
        approval_id: str,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """Wait for user to respond to approval request.

        Args:
            session_id: Research session ID
            approval_id: Approval ID to wait for
            timeout: Maximum wait time in seconds (None = wait forever)

        Returns:
            Approval response data

        Raises:
            TimeoutError: If timeout expires
            KeyError: If approval_id not found
        """
        if session_id not in self._approval_events:
            raise KeyError(f"No approvals for session {session_id}")

        if approval_id not in self._approval_events[session_id]:
            raise KeyError(f"Approval {approval_id} not found")

        event = self._approval_events[session_id][approval_id]

        try:
            if timeout:
                await asyncio.wait_for(event.wait(), timeout=timeout)
            else:
                await event.wait()
        except asyncio.TimeoutError:
            # Mark as timed out
            if session_id in self._pending_approvals and approval_id in self._pending_approvals[session_id]:
                self._pending_approvals[session_id][approval_id]["status"] = "timed_out"
            raise TimeoutError(f"Approval {approval_id} timed out after {timeout}s")

        # Get response
        response = self._approval_responses[session_id].get(approval_id)
        if not response:
            raise RuntimeError(f"Approval {approval_id} completed but no response found")

        return response

    def submit_approval_response(
        self,
        session_id: str,
        approval_id: str,
        decision: str,
        feedback: Optional[str] = None
    ) -> bool:
        """Submit user response to approval request.

        Args:
            session_id: Research session ID
            approval_id: Approval ID being responded to
            decision: "approve" or "reject"
            feedback: Optional user feedback

        Returns:
            True if response was accepted, False if approval not found
        """
        if session_id not in self._pending_approvals:
            return False

        if approval_id not in self._pending_approvals[session_id]:
            return False

        # Store response
        response = {
            "approval_id": approval_id,
            "decision": decision,
            "feedback": feedback,
            "responded_at": datetime.utcnow().isoformat()
        }

        self._approval_responses[session_id][approval_id] = response

        # Update status
        self._pending_approvals[session_id][approval_id]["status"] = "responded"

        # Signal waiting agent
        if approval_id in self._approval_events[session_id]:
            self._approval_events[session_id][approval_id].set()

        return True

    def get_pending_approvals(self, session_id: str) -> list[Dict[str, Any]]:
        """Get all pending approval requests for a session.

        Args:
            session_id: Research session ID

        Returns:
            List of pending approval requests
        """
        if session_id not in self._pending_approvals:
            return []

        return [
            approval
            for approval in self._pending_approvals[session_id].values()
            if approval["status"] == "pending"
        ]

    def cleanup_session(self, session_id: str):
        """Clean up all approval data for a session.

        Args:
            session_id: Research session ID
        """
        self._pending_approvals.pop(session_id, None)
        self._approval_events.pop(session_id, None)
        self._approval_responses.pop(session_id, None)


# Global instance
hitl_manager = HITLManager()
