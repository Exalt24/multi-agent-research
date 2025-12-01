"""LLM configuration with Ollama (local) + Groq (cloud) fallback."""

import os
from typing import Optional
from langchain_groq import ChatGroq
from langchain_community.llms import Ollama
from langchain_core.language_models import BaseLLM
from .config import get_settings

settings = get_settings()


class LLMManager:
    """Manages LLM instances with fallback logic."""

    def __init__(self):
        self._groq_llm: Optional[ChatGroq] = None
        self._ollama_llm: Optional[Ollama] = None

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

    def get_ollama_llm(self, temperature: float = 0.7) -> Ollama:
        """Get Ollama LLM instance (local, unlimited)."""
        if self._ollama_llm is None:
            self._ollama_llm = Ollama(
                base_url=settings.ollama_base_url,
                model=settings.local_llm_model,
                temperature=temperature,
            )
        return self._ollama_llm

    def get_llm(self, temperature: float = 0.7, prefer_local: bool = False) -> BaseLLM:
        """Get LLM with fallback logic.

        Args:
            temperature: LLM temperature
            prefer_local: If True, use Ollama first (for dev)

        Returns:
            LLM instance (Groq or Ollama)
        """
        # Production: always use Groq (cloud, reliable)
        if settings.is_production:
            try:
                return self.get_groq_llm(temperature)
            except Exception as e:
                print(f"Groq LLM failed: {e}, falling back to Ollama")
                return self.get_ollama_llm(temperature)

        # Development: prefer Ollama (local, unlimited, private)
        # Falls back to Groq if Ollama not running
        try:
            return self.get_ollama_llm(temperature)
        except Exception as e:
            print(f"Ollama not available: {e}, using Groq cloud")
            return self.get_groq_llm(temperature)


# Global LLM manager instance
_llm_manager = LLMManager()


def get_llm(temperature: float = 0.7, prefer_local: bool = False) -> BaseLLM:
    """Get LLM instance with fallback logic."""
    return _llm_manager.get_llm(temperature, prefer_local)


def get_groq_llm(temperature: float = 0.7) -> ChatGroq:
    """Get Groq LLM instance directly."""
    return _llm_manager.get_groq_llm(temperature)


def get_ollama_llm(temperature: float = 0.7) -> Ollama:
    """Get Ollama LLM instance directly."""
    return _llm_manager.get_ollama_llm(temperature)
