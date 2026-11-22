"""웹소켓으로 새 글 id만 알린다. 본문은 보내지 않는다."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(tags=["realtime"])


class Hub:
    def __init__(self) -> None:
        self._sockets: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._sockets.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self._sockets:
            self._sockets.remove(websocket)

    async def broadcast(self, payload: dict) -> None:
        stale: list[WebSocket] = []
        for socket in self._sockets:
            try:
                await socket.send_json(payload)
            except Exception:
                stale.append(socket)
        for socket in stale:
            self.disconnect(socket)


hub = Hub()


@router.websocket("/ws/posts")
async def posts_socket(websocket: WebSocket) -> None:
    await hub.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        hub.disconnect(websocket)
