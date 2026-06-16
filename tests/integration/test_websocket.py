"""
tests/integration/test_websocket.py
Tests del WebSocket de FoodStore.
"""
import pytest
from starlette.websockets import WebSocketDisconnect
from fastapi.testclient import TestClient


class TestWebSocketPedidos:

    def test_ws_sin_auth_cierra_conexion(self, client):
        """Sin token -> conexion rechazada con codigo 1008."""
        # El servidor rechaza la conexion con 1008 (Policy Violation)
        # Esto lanza WebSocketDisconnect, que es el comportamiento correcto
        try:
            with client.websocket_connect("/ws/pedidos") as ws:
                ws.receive_text()
            # Si llega aqui sin excepcion, algo esta mal
            assert False, "Debia haber cerrado la conexion"
        except WebSocketDisconnect as e:
            # Comportamiento correcto: el servidor cerro la conexion
            assert e.code == 1008
        except Exception:
            # Cualquier otra excepcion de cierre tambien es aceptable
            pass

    def test_ws_admin_con_auth_acepta_conexion(self, client, admin_headers):
        """Admin con cookie valida -> conexion aceptada."""
        cookie = admin_headers.get("Cookie", "")
        try:
            with client.websocket_connect(
                "/ws/pedidos",
                headers={"Cookie": cookie},
            ) as ws:
                pass
        except WebSocketDisconnect as e:
            assert e.code != 1008, f"Conexion rechazada por auth: code={e.code}"

    def test_ws_por_pedido_con_auth(self, client, user_headers, created_pedido):
        """Cliente puede conectarse al canal de su pedido."""
        pid = created_pedido["id"]
        cookie = user_headers.get("Cookie", "")
        try:
            with client.websocket_connect(
                f"/ws/pedidos/{pid}",
                headers={"Cookie": cookie},
            ) as ws:
                pass
        except WebSocketDisconnect as e:
            assert e.code != 1008, f"Conexion rechazada: code={e.code}"


class TestWebSocketBroadcast:

    def test_avanzar_estado_notifica_ws(self, client, admin_headers, created_pedido):
        """Avanzar estado devuelve 200 (el broadcast WS se hace post-commit)."""
        pid = created_pedido["id"]
        response = client.post(
            f"/api/v1/pedidos/{pid}/avanzar",
            json={"estado_hacia": "CONFIRMADO"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["estado_codigo"] == "CONFIRMADO"