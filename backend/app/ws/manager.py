"""WebSocket connection manager. broadcast() must never raise — pipeline nodes
call it mid-run and a dead socket must not kill a render.
"""
import json

from fastapi import WebSocket

from ..core.logging import get_logger

log = get_logger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.append(ws)

    def disconnect(self, ws: WebSocket) -> None:
        if ws in self._connections:
            self._connections.remove(ws)

    async def broadcast(self, event: dict) -> None:
        try:
            message = json.dumps(event, default=str)
        except Exception:
            log.exception("Unserializable WS event dropped")
            return

        dead: list[WebSocket] = []
        for ws in list(self._connections):
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()
