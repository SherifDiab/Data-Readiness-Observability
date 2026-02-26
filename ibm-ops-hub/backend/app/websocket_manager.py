"""
WebSocket connection manager for real-time dashboard updates.
Supports broadcast to all clients and selective component subscriptions.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import WebSocket

from app.cache import DateTimeEncoder

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections and broadcasts updates."""

    def __init__(self):
        self.active_connections: dict[WebSocket, set[str]] = {}

    async def connect(self, websocket: WebSocket, components: set[str] | None = None):
        await websocket.accept()
        self.active_connections[websocket] = components or set()
        logger.info(
            "WebSocket connected. Total connections: %d", len(self.active_connections)
        )

    def disconnect(self, websocket: WebSocket):
        self.active_connections.pop(websocket, None)
        logger.info(
            "WebSocket disconnected. Total connections: %d",
            len(self.active_connections),
        )

    async def broadcast(self, component: str, data: Any, msg_type: str = "update"):
        """Broadcast an update to all connected clients subscribed to this component."""
        message = json.dumps(
            {
                "type": msg_type,
                "component": component,
                "data": data,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            cls=DateTimeEncoder,
        )

        stale = []
        for ws, subscriptions in self.active_connections.items():
            if subscriptions and component not in subscriptions:
                continue
            try:
                await ws.send_text(message)
            except Exception:
                stale.append(ws)

        for ws in stale:
            self.disconnect(ws)

    async def send_heartbeat(self):
        """Send heartbeat to all connected clients."""
        message = json.dumps(
            {
                "type": "heartbeat",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        stale = []
        for ws in self.active_connections:
            try:
                await ws.send_text(message)
            except Exception:
                stale.append(ws)
        for ws in stale:
            self.disconnect(ws)


manager = ConnectionManager()
