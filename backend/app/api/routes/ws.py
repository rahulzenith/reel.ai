from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ...ws.manager import manager

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()  # keep-alive; inbound messages are ignored
    except WebSocketDisconnect:
        manager.disconnect(ws)
