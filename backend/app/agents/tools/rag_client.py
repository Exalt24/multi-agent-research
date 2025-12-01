"""RAG client to query Project 1's knowledge base."""

import httpx
from typing import Dict, Any, Optional


class RAGClient:
    """Client to query the Enterprise RAG Knowledge Base (Project 1)."""

    def __init__(self, base_url: str = "https://enterprise-rag-api.onrender.com/api"):
        self.base_url = base_url.rstrip("/")
        self.timeout = 30.0

    async def query(
        self,
        question: str,
        retrieval_strategy: str = "hybrid",
        max_chunks: int = 3
    ) -> Dict[str, Any]:
        """Query the RAG API.

        Args:
            question: Question to ask
            retrieval_strategy: Strategy to use (hybrid, vector, bm25, etc.)
            max_chunks: Maximum chunks to retrieve

        Returns:
            Dictionary with answer and sources
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/query",
                    json={
                        "question": question,
                        "retrieval_strategy": retrieval_strategy,
                        "max_chunks": max_chunks
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    return {
                        "answer": data.get("answer", ""),
                        "sources": data.get("sources", []),
                        "retrieval_strategy": data.get("retrieval_strategy", ""),
                        "success": True
                    }
                else:
                    return {
                        "answer": "",
                        "sources": [],
                        "error": f"API returned {response.status_code}",
                        "success": False
                    }

        except httpx.TimeoutException:
            return {
                "answer": "",
                "sources": [],
                "error": "RAG API timeout",
                "success": False
            }
        except Exception as e:
            return {
                "answer": "",
                "sources": [],
                "error": str(e),
                "success": False
            }

    async def health_check(self) -> bool:
        """Check if RAG API is available."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except:
            return False
