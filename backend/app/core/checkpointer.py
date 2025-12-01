"""Redis checkpointer for LangGraph state persistence."""

import os
from typing import Optional
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.redis import RedisSaver
import redis.asyncio as redis
from .config import get_settings

settings = get_settings()


class CheckpointerManager:
    """Manages checkpointer instances for LangGraph."""

    def __init__(self):
        self._redis_saver: Optional[RedisSaver] = None
        self._memory_saver: Optional[MemorySaver] = None

    async def get_redis_saver(self) -> RedisSaver:
        """Get Redis checkpointer (production)."""
        if self._redis_saver is None:
            # Parse Redis URL
            redis_client = await redis.from_url(
                settings.redis_url,
                password=settings.redis_password or None,
                encoding="utf-8",
                decode_responses=True
            )
            self._redis_saver = RedisSaver(redis_client)
        return self._redis_saver

    def get_memory_saver(self) -> MemorySaver:
        """Get in-memory checkpointer (development)."""
        if self._memory_saver is None:
            self._memory_saver = MemorySaver()
        return self._memory_saver

    async def get_checkpointer(self):
        """Get checkpointer based on environment.

        Returns Redis in production, Memory in development.
        """
        if settings.is_production and settings.redis_url:
            try:
                return await self.get_redis_saver()
            except Exception as e:
                print(f"Redis checkpointer failed: {e}, using memory")
                return self.get_memory_saver()
        else:
            return self.get_memory_saver()


# Global checkpointer manager
_checkpointer_manager = CheckpointerManager()


async def get_checkpointer():
    """Get checkpointer instance."""
    return await _checkpointer_manager.get_checkpointer()
