"""Base agent class with retry logic and error handling."""

import asyncio
import time
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from langchain_core.language_models import BaseLLM
from langchain_core.tools import BaseTool
from .state import MarketResearchState


class BaseAgent(ABC):
    """Base class for all research agents.

    Provides common functionality:
    - Retry logic with exponential backoff
    - Error handling and logging
    - Token/cost tracking
    - WebSocket status updates
    """

    def __init__(
        self,
        name: str,
        llm: BaseLLM,
        tools: Optional[List[BaseTool]] = None,
        max_retries: int = 3,
        timeout: int = 120,
    ):
        self.name = name
        self.llm = llm
        self.tools = tools or []
        self.max_retries = max_retries
        self.timeout = timeout
        self._websocket_callback = None

    def set_websocket_callback(self, callback):
        """Set callback for WebSocket updates."""
        self._websocket_callback = callback

    async def _emit_status(
        self,
        status: str,
        progress: int,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ):
        """Emit status update via WebSocket."""
        if self._websocket_callback:
            await self._websocket_callback({
                "type": "agent_progress",
                "agent": self.name,
                "status": status,
                "progress": progress,
                "message": message,
                "data": data or {},
                "timestamp": time.time()
            })

    async def execute(self, state: MarketResearchState) -> Dict[str, Any]:
        """Execute agent with retry logic.

        Args:
            state: Current workflow state

        Returns:
            Updated state fields
        """
        await self._emit_status("running", 0, f"{self.name} starting...")

        for attempt in range(self.max_retries):
            try:
                # Execute agent logic with timeout
                result = await asyncio.wait_for(
                    self._process(state),
                    timeout=self.timeout
                )

                await self._emit_status("completed", 100, f"{self.name} completed successfully")
                return result

            except asyncio.TimeoutError:
                error_msg = f"{self.name} timed out after {self.timeout}s"
                if attempt < self.max_retries - 1:
                    await self._emit_status("retrying", 50, error_msg)
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    await self._emit_status("failed", 100, error_msg)
                    return self._handle_error(error_msg, state)

            except Exception as e:
                error_msg = f"{self.name} error: {str(e)}"
                if attempt < self.max_retries - 1:
                    await self._emit_status("retrying", 50, error_msg)
                    await asyncio.sleep(2 ** attempt)
                else:
                    await self._emit_status("failed", 100, error_msg)
                    return self._handle_error(error_msg, state)

        return self._handle_error(f"{self.name} failed after {self.max_retries} attempts", state)

    @abstractmethod
    async def _process(self, state: MarketResearchState) -> Dict[str, Any]:
        """Process agent logic. Must be implemented by subclasses.

        Args:
            state: Current workflow state

        Returns:
            Dictionary with state updates
        """
        pass

    def _handle_error(self, error_msg: str, state: MarketResearchState) -> Dict[str, Any]:
        """Handle error and return error state update."""
        return {
            "errors": [{
                "agent": self.name,
                "error": error_msg,
                "timestamp": time.time()
            }],
            "current_agent": self.name,
        }

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation (4 chars ≈ 1 token)."""
        return len(text) // 4

    def _track_cost(self, input_text: str, output_text: str) -> Dict[str, Any]:
        """Track token usage and estimated cost.

        Groq free tier, so cost is $0, but track tokens for monitoring.
        """
        input_tokens = self._estimate_tokens(input_text)
        output_tokens = self._estimate_tokens(output_text)

        return {
            "agent": self.name,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "estimated_cost_usd": 0.0,  # Free tier
            "timestamp": time.time()
        }
