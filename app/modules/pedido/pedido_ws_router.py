from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from app.core.security import decode_access_token
from app.core.ws_manager import manager

pedido_ws_router = APIRouter(tags=["Pedidos WebSocket"])


def _authenticate_ws(websocket: WebSocket) -> bool:
    """Valida el token JWT desde la cookie de la conexión WebSocket."""
    token = websocket.cookies.get("access_token")
    if not token:
        return False
    payload = decode_access_token(token)
    return payload is not None


@pedido_ws_router.websocket("/ws/pedidos")
async def ws_pedidos_admin(websocket: WebSocket):
    """Canal global: admin-app recibe todos los cambios de estado."""
    if not _authenticate_ws(websocket):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect_admin(websocket)
    try:
        while True:
            # Mantiene la conexión abierta; el servidor solo emite, no recibe
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@pedido_ws_router.websocket("/ws/pedidos/{pedido_id}")
async def ws_pedido_cliente(websocket: WebSocket, pedido_id: int):
    """Canal por pedido: store-app escucha cambios de un pedido específico."""
    if not _authenticate_ws(websocket):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect_pedido(pedido_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
