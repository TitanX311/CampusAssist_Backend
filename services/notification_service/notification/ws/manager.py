"""
In-process WebSocket connection manager.

Maintains a mapping of  user_id → set[WebSocket]  so that when the gRPC
servicer persists a notification it can immediately push it to any currently
connected client (e.g. an Android app in the foreground).

Thread-safety / concurrency notes
----------------------------------
* The manager is a plain Python object shared between the FastAPI ASGI
  worker and the gRPC asyncio server.  Both run in the same event loop,
  so there are no threading issues — all operations are cooperative.
* WebSocket sends are best-effort.  If a send raises (the socket was
  closed between our membership check and the send), we silently remove
  the dead connection and move on.  Persistence to Postgres is the
  authoritative store; WS delivery is an optimistic fast-path.

Usage
-----
    from notification.ws.manager import ws_manager

    # In a WebSocket route:
    await ws_manager.connect(user_id, websocket)
    try:
        while True:
            text = await websocket.receive_text()
            if text == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(user_id, websocket)

    # In the gRPC servicer (after DB persist):
    await ws_manager.push(user_id, notification_dict)
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections keyed by user_id."""

    def __init__(self) -> None:
        # user_id (str) → set of live WebSocket connections
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, user_id: str, websocket: WebSocket) -> None:
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self._connections[user_id].add(websocket)
        logger.debug("WS connected: user=%s  total=%d", user_id, len(self._connections[user_id]))

    def disconnect(self, user_id: str, websocket: WebSocket) -> None:
        """Remove a WebSocket from the registry (call on disconnect)."""
        self._connections[user_id].discard(websocket)
        if not self._connections[user_id]:
            self._connections.pop(user_id, None)
        logger.debug("WS disconnected: user=%s", user_id)

    async def push(self, user_id: str, data: dict[str, Any]) -> int:
        """Push a JSON payload to all active connections for *user_id*.

        Returns the number of connections that successfully received the
        message.  Dead sockets are silently pruned from the registry.
        """
        sockets = list(self._connections.get(user_id, set()))
        if not sockets:
            return 0

        dead: list[WebSocket] = []
        sent = 0
        for ws in sockets:
            try:
                await ws.send_json(data)
                sent += 1
            except Exception as exc:
                logger.debug("WS send failed for user=%s: %s", user_id, exc)
                dead.append(ws)

        for ws in dead:
            self._connections[user_id].discard(ws)
        if not self._connections[user_id]:
            self._connections.pop(user_id, None)

        return sent

    def active_user_ids(self) -> list[str]:
        """Return a snapshot of user IDs with at least one open connection."""
        return list(self._connections.keys())

    def connection_count(self) -> int:
        """Total number of open WebSocket connections across all users."""
        return sum(len(v) for v in self._connections.values())


# Module-level singleton — imported by routes and gRPC servicer alike.
ws_manager = ConnectionManager()
