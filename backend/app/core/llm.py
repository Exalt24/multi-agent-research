"""LLM configuration with Ollama (local) + Groq (cloud) fallback."""

from typing import Optional
from langchain_groq import ChatGroq
from langchain_ollama import OllamaLLM
from langchain_core.language_models import BaseLLM
from .config import get_settings

settings = get_settings()


class LLMManager:
    """Manages LLM instances with fallback logic."""

    def __init__(self):
        self._groq_llm: Optional[ChatGroq] = None
        self._ollama_llm: Optional[OllamaLLM] = None

    def get_groq_llm(self, temperature: float = 0.7) -> ChatGroq:
        """Get Groq LLM instance (cloud, fast)."""
        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY not set in environment")

        if self._groq_llm is None:
            self._groq_llm = ChatGroq(
                api_key=settings.groq_api_key,
                model_name=settings.default_llm_model,
                temperature=temperature,
                max_tokens=4096,
            )
        return self._groq_llm

    def get_ollama_llm(self, temperature: float = 0.7) -> OllamaLLM:
        """Get Ollama LLM instance (local, unlimited)."""
        if self._ollama_llm is None:
            self._ollama_llm = OllamaLLM(
                base_url=settings.ollama_base_url,
                model=settings.local_llm_model,
                temperature=temperature,
                num_predict=4096,  # Match Groq's max_tokens for consistency
            )
        return self._ollama_llm

    def get_llm(self, temperature: float = 0.7) -> BaseLLM:
        """Get LLM with automatic fallback logic based on environment.

        Args:
            temperature: LLM temperature (0.0-1.0)

        Returns:
            LLM instance (Groq in production, Ollama in development with Groq fallback)

        Behavior:
            - Production: Groq only (fail-fast if unavailable)
            - Development: Ollama first, falls back to Groq if Ollama not running
        """
        # Production: Use Groq only (Render doesn't have Ollama installed)
        if settings.is_production:
            return self.get_groq_llm(temperature)

        # Development: Prefer Ollama (local, unlimited, private)
        # Falls back to Groq if Ollama not running
        try:
            return self.get_ollama_llm(temperature)
        except Exception as e:
            print(f"[!] Ollama not available: {e}")
            print("[i] Falling back to Groq cloud API")
            return self.get_groq_llm(temperature)

    def health_check(self) -> dict:
        """Check which LLM providers are available.

        Returns:
            Dictionary with provider availability status

        Example:
            >>> manager.health_check()
            {
                "groq_configured": True,
                "ollama_available": True,
                "active_provider": "ollama",
                "environment": "development"
            }
        """
        groq_configured = bool(settings.groq_api_key)
        ollama_available = False

        # Check if Ollama is actually running
        if settings.use_ollama:
            ollama_available = settings.check_ollama_health()

        # Determine active provider
        if settings.is_production:
            active = "groq"
        else:
            active = "ollama" if ollama_available else "groq"

        return {
            "groq_configured": groq_configured,
            "ollama_available": ollama_available,
            "active_provider": active,
            "environment": settings.environment,
            "groq_model": settings.default_llm_model,
            "ollama_model": settings.local_llm_model
        }


# Global LLM manager instance
_llm_manager = LLMManager()


def get_llm(temperature: float = 0.7) -> BaseLLM:
    """Get LLM instance with automatic fallback logic.

    Returns appropriate LLM based on environment:
    - Production: Groq (cloud, reliable)
    - Development: Ollama first, Groq fallback
    """
    return _llm_manager.get_llm(temperature)


def get_groq_llm(temperature: float = 0.7) -> ChatGroq:
    """Get Groq LLM instance directly."""
    return _llm_manager.get_groq_llm(temperature)


def get_ollama_llm(temperature: float = 0.7) -> OllamaLLM:
    """Get Ollama LLM instance directly."""
    return _llm_manager.get_ollama_llm(temperature)


def llm_health_check() -> dict:
    """Check LLM provider availability.

    Returns:
        Dictionary with provider status and configuration
    """
    return _llm_manager.health_check()
