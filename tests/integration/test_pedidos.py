"""
tests/integration/test_pedidos.py
Tests del modulo de pedidos: CRUD, FSM, historial.
"""
import pytest
from fastapi.testclient import TestClient


class TestCrearPedido:

    def test_crear_pedido_exitoso(self, client, user_headers, created_producto):
        response = client.post(
            "/api/v1/pedidos/",
            json={
                "forma_pago_codigo": "EFECTIVO",
                "items": [{"producto_id": created_producto["id"], "cantidad": 2, "personalizacion": []}],
            },
            headers=user_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["estado_codigo"] == "PENDIENTE"
        assert data["subtotal"] > 0

    def test_crear_sin_auth_returns_401(self, client, created_producto):
        response = client.post(
            "/api/v1/pedidos/",
            json={"forma_pago_codigo": "EFECTIVO", "items": [{"producto_id": created_producto["id"], "cantidad": 1}]},
        )
        assert response.status_code == 401

    def test_crear_sin_items_returns_422(self, client, user_headers):
        response = client.post(
            "/api/v1/pedidos/",
            json={"forma_pago_codigo": "EFECTIVO", "items": []},
            headers=user_headers,
        )
        assert response.status_code == 422

    def test_crear_producto_inexistente_returns_404(self, client, user_headers):
        response = client.post(
            "/api/v1/pedidos/",
            json={"forma_pago_codigo": "EFECTIVO", "items": [{"producto_id": 99999, "cantidad": 1}]},
            headers=user_headers,
        )
        assert response.status_code == 404

    def test_crear_forma_pago_invalida_returns_400(self, client, user_headers, created_producto):
        response = client.post(
            "/api/v1/pedidos/",
            json={"forma_pago_codigo": "INVALIDA", "items": [{"producto_id": created_producto["id"], "cantidad": 1}]},
            headers=user_headers,
        )
        assert response.status_code == 400

    def test_snapshot_precio_inmutable(self, client, user_headers, created_producto):
        response = client.post(
            "/api/v1/pedidos/",
            json={"forma_pago_codigo": "EFECTIVO", "items": [{"producto_id": created_producto["id"], "cantidad": 1}]},
            headers=user_headers,
        )
        assert response.status_code == 201
        pid = response.json()["id"]
        detalle = client.get(f"/api/v1/pedidos/{pid}", headers=user_headers)
        assert detalle.status_code == 200
        detalles = detalle.json()["detalles"]
        assert detalles[0]["precio_snapshot"] == created_producto["precio_base"]
        assert detalles[0]["nombre_snapshot"] == created_producto["nombre"]


class TestListarPedidos:

    def test_client_ve_sus_pedidos(self, client, user_headers, created_pedido):
        response = client.get("/api/v1/pedidos/", headers=user_headers)
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_admin_ve_todos(self, client, admin_headers, created_pedido):
        response = client.get("/api/v1/pedidos/", headers=admin_headers)
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_sin_auth_returns_401(self, client):
        response = client.get("/api/v1/pedidos/")
        assert response.status_code == 401


class TestObtenerPedido:

    def test_obtener_pedido_propio(self, client, user_headers, created_pedido):
        pid = created_pedido["id"]
        response = client.get(f"/api/v1/pedidos/{pid}", headers=user_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == pid
        assert "detalles" in data
        assert "historial" in data

    def test_obtener_inexistente_returns_404(self, client, admin_headers):
        response = client.get("/api/v1/pedidos/999999", headers=admin_headers)
        assert response.status_code == 404


class TestFSMPedido:

    def test_avanzar_estado_valido(self, client, admin_headers, created_pedido):
        pid = created_pedido["id"]
        response = client.post(
            f"/api/v1/pedidos/{pid}/avanzar",
            json={"estado_hacia": "CONFIRMADO"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["estado_codigo"] == "CONFIRMADO"

    def test_transicion_invalida_returns_409(self, client, admin_headers, created_pedido):
        pid = created_pedido["id"]
        response = client.post(
            f"/api/v1/pedidos/{pid}/avanzar",
            json={"estado_hacia": "ENTREGADO"},
            headers=admin_headers,
        )
        assert response.status_code == 409

    def test_estado_terminal_no_permite_transicion(self, client, admin_headers, created_pedido):
        pid = created_pedido["id"]
        client.post(
            f"/api/v1/pedidos/{pid}/avanzar",
            json={"estado_hacia": "CANCELADO", "motivo": "Test"},
            headers=admin_headers,
        )
        response = client.post(
            f"/api/v1/pedidos/{pid}/avanzar",
            json={"estado_hacia": "CONFIRMADO"},
            headers=admin_headers,
        )
        assert response.status_code == 409

    def test_cancelar_sin_motivo_returns_400(self, client, admin_headers, created_pedido):
        pid = created_pedido["id"]
        response = client.post(
            f"/api/v1/pedidos/{pid}/avanzar",
            json={"estado_hacia": "CANCELADO"},
            headers=admin_headers,
        )
        assert response.status_code == 400

    def test_client_no_puede_avanzar_estado(self, client, user_headers, created_pedido):
        pid = created_pedido["id"]
        response = client.post(
            f"/api/v1/pedidos/{pid}/avanzar",
            json={"estado_hacia": "CONFIRMADO"},
            headers=user_headers,
        )
        assert response.status_code == 403

    def test_client_puede_cancelar_pendiente(self, client, user_headers, created_pedido):
        pid = created_pedido["id"]
        response = client.post(
            f"/api/v1/pedidos/{pid}/avanzar",
            json={"estado_hacia": "CANCELADO", "motivo": "No lo quiero"},
            headers=user_headers,
        )
        assert response.status_code == 200
        assert response.json()["estado_codigo"] == "CANCELADO"

    def test_flujo_completo_fsm_v7(self, client, admin_headers, created_pedido):
        pid = created_pedido["id"]
        for estado in ["CONFIRMADO", "EN_PREP", "ENTREGADO"]:
            r = client.post(
                f"/api/v1/pedidos/{pid}/avanzar",
                json={"estado_hacia": estado},
                headers=admin_headers,
            )
            assert r.status_code == 200, f"Fallo en {estado}: {r.json()}"
            assert r.json()["estado_codigo"] == estado


class TestHistorialPedido:

    def test_historial_tiene_entrada_inicial(self, client, user_headers, created_pedido):
        pid = created_pedido["id"]
        response = client.get(f"/api/v1/pedidos/{pid}/historial", headers=user_headers)
        assert response.status_code == 200
        historial = response.json()
        assert len(historial) >= 1
        primer_registro = historial[0]
        assert primer_registro["estado_desde"] is None
        assert primer_registro["estado_hacia"] == "PENDIENTE"

    def test_historial_crece_con_transiciones(self, client, admin_headers, created_pedido):
        pid = created_pedido["id"]
        client.post(
            f"/api/v1/pedidos/{pid}/avanzar",
            json={"estado_hacia": "CONFIRMADO"},
            headers=admin_headers,
        )
        response = client.get(f"/api/v1/pedidos/{pid}/historial", headers=admin_headers)
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_historial_ordenado_asc(self, client, admin_headers, created_pedido):
        pid = created_pedido["id"]
        for estado in ["CONFIRMADO", "EN_PREP"]:
            client.post(
                f"/api/v1/pedidos/{pid}/avanzar",
                json={"estado_hacia": estado},
                headers=admin_headers,
            )
        response = client.get(f"/api/v1/pedidos/{pid}/historial", headers=admin_headers)
        historial = response.json()
        estados = [h["estado_hacia"] for h in historial]
        assert estados == ["PENDIENTE", "CONFIRMADO", "EN_PREP"]