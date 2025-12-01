"""WebSocket manager for real-time agent status updates."""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
import asyncio


class WebSocketManager:
    """Manages WebSocket connections for real-time updates."""

    def __init__(self):
        # session_id -> Set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, session_id: str):
        """Accept a WebSocket connection for a session.

        Args:
            websocket: The WebSocket connection
            session_id: Research session ID
        """
        await websocket.accept()
        async with self._lock:
            if session_id not in self.active_connections:
                self.active_connections[session_id] = set()
            self.active_connections[session_id].add(websocket)

        print(f"WebSocket connected for session {session_id}")

    async def disconnect(self, websocket: WebSocket, session_id: str):
        """Remove a WebSocket connection.

        Args:
            websocket: The WebSocket connection
            session_id: Research session ID
        """
        async with self._lock:
            if session_id in self.active_connections:
                self.active_connections[session_id].discard(websocket)
                if not self.active_connections[session_id]:
                    del self.active_connections[session_id]

        print(f"WebSocket disconnected for session {session_id}")

    async def send_update(self, session_id: str, message: dict):
        """Send update to all connected clients for a session.

        Args:
            session_id: Research session ID
            message: Update message to send
        """
        async with self._lock:
            connections = self.active_connections.get(session_id, set()).copy()

        if connections:
            # Prepare message
            json_message = json.dumps(message)

            # Send to all connections
            disconnected = []
            for connection in connections:
                try:
                    await connection.send_text(json_message)
                except WebSocketDisconnect:
                    disconnected.append(connection)
                except Exception as e:
                    print(f"Error sending WebSocket message: {e}")
                    disconnected.append(connection)

            # Clean up disconnected clients
            if disconnected:
                async with self._lock:
                    for conn in disconnected:
                        if session_id in self.active_connections:
                            self.active_connections[session_id].discard(conn)

    async def broadcast_agent_status(
        self,
        session_id: str,
        agent: str,
        status: str,
        progress: int,
        message: str,
        data: dict = None
    ):
        """Broadcast agent status update.

        Args:
            session_id: Research session ID
            agent: Agent name
            status: Status (running, completed, failed, etc.)
            progress: Progress percentage (0-100)
            message: Status message
            data: Optional additional data
        """
        await self.send_update(session_id, {
            "type": "agent_status",
            "session_id": session_id,
            "agent": agent,
            "status": status,
            "progress": progress,
            "message": message,
            "data": data or {},
            "timestamp": asyncio.get_event_loop().time()
        })


# Global WebSocket manager instance
ws_manager = WebSocketManager()


def get_ws_manager() -> WebSocketManager:
    """Get the global WebSocket manager instance."""
    return ws_manager
