"""Application configuration using Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Secrets (MUST be in .env)
    groq_api_key: str = ""
    tavily_api_key: str = ""
    redis_url: str = ""
    environment: str = "development"

    # Constants (hardcoded defaults, rarely change)
    ollama_base_url: str = "http://localhost:11434"
    rag_api_url: str = "https://enterprise-rag-api.onrender.com/api"
    default_llm_model: str = "llama3.3-70b-versatile"
    local_llm_model: str = "llama3"
    log_level: str = "INFO"
    max_parallel_agents: int = 2
    agent_timeout: int = 120

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3001"]

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"

    @property
    def use_ollama(self) -> bool:
        """Check if Ollama is available (not production)."""
        return not self.is_production


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
