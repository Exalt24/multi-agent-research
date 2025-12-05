"""Application configuration using Pydantic Settings."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Secrets (MUST be in .env)
    groq_api_key: str = Field(default="", description="Groq API key for cloud LLM")
    tavily_api_key: str = Field(default="", description="Tavily API key for web search")
    redis_url: str = Field(default="", description="Redis URL for search result caching (optional)")
    environment: str = "development"

    # Constants (hardcoded defaults, rarely change)
    ollama_base_url: str = "http://localhost:11434"
    rag_api_url: str = "https://enterprise-rag-api.onrender.com/api"
    default_llm_model: str = "llama-3.3-70b-versatile"
    local_llm_model: str = "llama3"
    log_level: str = "INFO"
    agent_timeout: int = 120

    # Parallel execution
    max_parallel_agents: int = Field(default=2, description="Max agents to run in parallel")

    # Cache configuration
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds (1 hour)")
    redis_max_connections: int = Field(default=10, description="Max Redis connections in pool")

    # CORS configuration
    cors_origins_env: str = Field(default="", description="Comma-separated list of additional CORS origins")

    @property
    def cors_origins(self) -> list[str]:
        """Get CORS origins from environment and defaults."""
        base_origins = [
            "http://localhost:3000",
            "http://localhost:3001",
        ]
        # Add production origins from environment variable
        if self.cors_origins_env:
            additional = [origin.strip() for origin in self.cors_origins_env.split(",")]
            base_origins.extend(additional)
        return base_origins

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"

    @property
    def use_ollama(self) -> bool:
        """Check if Ollama should be used (development only)."""
        # In production, never use Ollama (not installed on Render)
        return not self.is_production

    def check_ollama_health(self) -> bool:
        """Check if Ollama service is running and accessible."""
        try:
            import requests
            response = requests.get(
                f"{self.ollama_base_url}/api/tags",
                timeout=2
            )
            is_healthy = response.status_code == 200
            if is_healthy:
                logger.info(f"Ollama is available at {self.ollama_base_url}")
            return is_healthy
        except Exception as e:
            logger.warning(f"Ollama not available at {self.ollama_base_url}: {e}")
            return False

    def validate_requirements(self) -> None:
        """Validate that required configuration is present."""
        errors = []

        # In production, API keys are required
        if self.is_production:
            if not self.groq_api_key:
                errors.append("GROQ_API_KEY is required in production")
            if not self.tavily_api_key:
                errors.append("TAVILY_API_KEY is required in production")

        # In development, at least one LLM provider must be available
        if not self.is_production:
            has_groq = bool(self.groq_api_key)
            has_ollama = self.check_ollama_health()
            if not has_groq and not has_ollama:
                errors.append(
                    "Either GROQ_API_KEY must be set or Ollama must be running at "
                    f"{self.ollama_base_url}"
                )

        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            raise ValueError(error_msg)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
