"""Base agent class with retry logic and error handling."""

import asyncio
import logging
import re
import time
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from langchain_core.language_models import BaseLLM
from .state import MarketResearchState
from ..core.tokens import count_tokens, estimate_cost

logger = logging.getLogger(__name__)


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
        max_retries: int = 5,
        timeout: int = 120,
        ws_manager = None,  # WebSocket manager
    ):
        self.name = name
        self.llm = llm
        self.max_retries = max_retries
        self.timeout = timeout
        self._ws_manager = ws_manager
        self._session_id = None
        self._fallback_index = 0

    def _get_model_name(self) -> str:
        """Detect the actual model name being used by this agent's LLM.

        Returns:
            Model name for tiktoken (e.g., "openai/gpt-oss-120b" or "llama3")

        Note:
            Different LLM providers store model name in different attributes:
            - ChatGroq: model_name attribute
            - OllamaLLM: model attribute
        """
        # Try common attribute names
        if hasattr(self.llm, "model_name"):
            return self.llm.model_name
        elif hasattr(self.llm, "model"):
            return self.llm.model
        else:
            # Fallback to default if can't detect
            from ..core.config import get_settings
            settings = get_settings()
            return settings.default_llm_model

    async def _emit_status(
        self,
        status: str,
        progress: int,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ):
        """Emit status update via WebSocket."""
        if self._ws_manager and self._session_id:
            await self._ws_manager.broadcast_agent_status(
                session_id=self._session_id,
                agent=self.name,
                status=status,
                progress=progress,
                message=message,
                data=data or {}
            )

    async def _request_approval(
        self,
        approval_id: str,
        question: str,
        context: Optional[Dict[str, Any]] = None,
        options: Optional[List[str]] = None,
        timeout: Optional[float] = 300  # 5 minutes default
    ) -> Dict[str, Any]:
        """Request human approval and wait for response.

        Args:
            approval_id: Unique approval ID
            question: Question to ask user
            context: Additional context data
            options: Available options (default: ["Approve", "Reject"])
            timeout: Max wait time in seconds (default: 300s = 5min)

        Returns:
            Approval response with decision and feedback

        Raises:
            TimeoutError: If user doesn't respond within timeout
            RuntimeError: If WebSocket manager not available

        Example:
            >>> response = await self._request_approval(
            ...     approval_id="fact-check-approval",
            ...     question="3 claims failed verification. Continue anyway?",
            ...     context={"failed_claims": 3, "total_claims": 10}
            ... )
            >>> if response["decision"] == "approve":
            ...     # Continue workflow
        """
        if not self._ws_manager or not self._session_id:
            raise RuntimeError("WebSocket manager not available for HITL")

        from ..services.hitl_manager import hitl_manager

        # Create approval request
        approval_data = hitl_manager.create_approval_request(
            session_id=self._session_id,
            approval_id=approval_id,
            agent=self.name,
            question=question,
            context=context,
            options=options
        )

        # Send to frontend via WebSocket
        await self._ws_manager.send_approval_request(
            session_id=self._session_id,
            approval_id=approval_id,
            agent=self.name,
            question=question,
            context=context,
            options=options
        )

        # Update agent status
        await self._emit_status(
            "waiting_approval",
            50,
            f"Waiting for human approval: {question[:50]}..."
        )

        # Wait for user response
        response = await hitl_manager.wait_for_approval(
            session_id=self._session_id,
            approval_id=approval_id,
            timeout=timeout
        )

        return response

    # Provider errors arrive as one long JSON blob. Never put that on a user's
    # screen: parse what we need out of it and show a plain sentence instead.
    _RETRY_AFTER_RE = re.compile(r"try again in ([0-9]+(?:\.[0-9]+)?)s")

    def _retry_delay(self, exc: Exception, attempt: int) -> float:
        """Seconds to wait before the next attempt.

        A provider rate limit tells us exactly how long to wait, and that wait
        is usually far longer than a plain exponential backoff, so honour it.
        """
        match = self._RETRY_AFTER_RE.search(str(exc))
        if match:
            return min(float(match.group(1)) + 1.0, 30.0)
        return float(2 ** attempt)

    def _is_rate_limit(self, exc: Exception) -> bool:
        lowered = str(exc).lower()
        return "rate_limit_exceeded" in lowered or "rate limit" in lowered

    def _try_next_model(self) -> Optional[str]:
        """Move this agent onto the next fallback model.

        Groq meters per model, per minute AND per day, so a daily ceiling on
        one model is not something waiting can fix. Another model is a separate
        bucket, which is why this is a model switch rather than a longer sleep.

        Returns the new model name, or None when the chain is used up.
        """
        from ..core.config import get_settings

        chain = get_settings().fallback_llm_model_list
        while self._fallback_index < len(chain):
            candidate = chain[self._fallback_index]
            self._fallback_index += 1
            try:
                from ..core.llm import get_groq_llm_for_model

                self.llm = get_groq_llm_for_model(candidate)
                logger.warning("%s falling back to model %s", self.name, candidate)
                return candidate
            except Exception as e:  # a bad name in the chain must not end the run
                logger.warning("%s could not switch to %s: %s", self.name, candidate, e)
        return None

    def _user_error(self, exc: Exception) -> str:
        """A short, safe message for the UI. Full detail goes to the log."""
        text = str(exc)
        lowered = text.lower()
        if "rate_limit_exceeded" in lowered or "rate limit" in lowered:
            wait = self._RETRY_AFTER_RE.search(text)
            suffix = f" (retrying in ~{round(float(wait.group(1)))}s)" if wait else ""
            return f"{self.name} hit the model provider's rate limit{suffix}"
        if "model_not_found" in lowered or "does not exist" in lowered:
            return f"{self.name} could not reach the configured model"
        if "timeout" in lowered or "timed out" in lowered:
            return f"{self.name} timed out talking to the model"
        return f"{self.name} could not complete this step"

    async def execute(self, state: MarketResearchState) -> Dict[str, Any]:
        """Execute agent with retry logic.

        Args:
            state: Current workflow state

        Returns:
            Updated state fields
        """
        # Extract session_id from state for WebSocket updates
        self._session_id = state.get("session_id", "")

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
                logger.warning("%s attempt %d failed: %s", self.name, attempt + 1, e)
                user_msg = self._user_error(e)
                if attempt < self.max_retries - 1:
                    switched = self._try_next_model() if self._is_rate_limit(e) else None
                    if switched:
                        await self._emit_status(
                            "retrying", 50,
                            f"{self.name} switching to a backup model"
                        )
                        continue
                    await self._emit_status("retrying", 50, user_msg)
                    await asyncio.sleep(self._retry_delay(e, attempt))
                else:
                    await self._emit_status("failed", 100, user_msg)
                    return self._handle_error(user_msg, state)

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
        # Make error messages user-friendly
        user_friendly_msg = error_msg
        if "rate_limit" in error_msg.lower():
            user_friendly_msg = f"{self.name}: Rate limit reached. Please try again in a few minutes."
        elif "404" in error_msg and "model" in error_msg.lower():
            user_friendly_msg = f"{self.name}: Model not available. Please check configuration."
        else:
            # Truncate very long error messages
            user_friendly_msg = error_msg[:200] + "..." if len(error_msg) > 200 else error_msg

        return {
            "errors": [{
                "agent": self.name,
                "error": user_friendly_msg,
                "timestamp": time.time()
            }],
            "current_agent": [self.name],  # List for operator.add
        }

    def _count_tokens(self, text: str, model_name: Optional[str] = None) -> int:
        """Count tokens accurately using tiktoken with auto-detected model.

        Args:
            text: Text to tokenize
            model_name: Model name (auto-detects from self.llm if not provided)

        Returns:
            Exact token count

        Note:
            Automatically detects which model this agent is using (Groq or Ollama)
            and uses that for accurate tokenization. Critical for correct cost tracking.
        """
        if model_name is None:
            model_name = self._get_model_name()
        return count_tokens(text, model_name)

    def _track_cost(self, input_text: str, output_text: str, model_name: Optional[str] = None) -> Dict[str, Any]:
        """Track token usage and estimated cost using tiktoken with auto-detected model.

        Args:
            input_text: Prompt text sent to LLM
            output_text: Response text from LLM
            model_name: Model name (auto-detects from self.llm if not provided)

        Returns:
            Dictionary with token counts and cost estimate

        Note:
            Automatically detects which model this agent is using:
            - Development: "llama3" (Ollama model)
            - Production: settings.default_llm_model (Groq model)

            This ensures accurate token counting and cost tracking for the actual model in use.
        """
        # Auto-detect model if not provided
        if model_name is None:
            model_name = self._get_model_name()

        input_tokens = self._count_tokens(input_text, model_name)
        output_tokens = self._count_tokens(output_text, model_name)
        total_tokens = input_tokens + output_tokens

        cost = estimate_cost(total_tokens, model_name)

        return {
            "agent": self.name,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "estimated_cost_usd": cost,
            "model_name": model_name,
            "timestamp": time.time()
        }
