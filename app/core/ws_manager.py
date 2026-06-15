from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        # Canal global: admin-app recibe todos los cambios
        self._admin_connections: list[WebSocket] = []
        # Canal por pedido: store-app escucha solo su pedido
        self._pedido_connections: dict[int, list[WebSocket]] = {}

    async def connect_admin(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._admin_connections.append(websocket)

    async def connect_pedido(self, pedido_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self._pedido_connections.setdefault(pedido_id, []).append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self._admin_connections:
            self._admin_connections.remove(websocket)
        for connections in self._pedido_connections.values():
            if websocket in connections:
                connections.remove(websocket)

    async def broadcast_all(self, message: dict) -> None:
        dead: list[WebSocket] = []
        for ws in list(self._admin_connections):
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    async def broadcast_pedido(self, pedido_id: int, message: dict) -> None:
        connections = self._pedido_connections.get(pedido_id, [])
        dead: list[WebSocket] = []
        for ws in list(connections):
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()
