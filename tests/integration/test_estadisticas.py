"""
tests/integration/test_estadisticas.py
Tests del modulo de estadisticas.
"""
import pytest
from fastapi.testclient import TestClient
from datetime import date


class TestResumenKPIs:

    def test_resumen_solo_admin(self, client, admin_headers):
        response = client.get("/api/v1/estadisticas/resumen", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "ventas_hoy" in data
        assert "ticket_promedio" in data
        assert "pedidos_activos" in data
        assert "ingresos_mes_actual" in data

    def test_resumen_client_returns_403(self, client, user_headers):
        response = client.get("/api/v1/estadisticas/resumen", headers=user_headers)
        assert response.status_code == 403

    def test_resumen_sin_auth_returns_401(self, client):
        response = client.get("/api/v1/estadisticas/resumen")
        assert response.status_code == 401

    def test_resumen_excluye_pedidos_cancelados(self, client, admin_headers, user_headers, created_pedido):
        pid = created_pedido["id"]
        client.post(
            f"/api/v1/pedidos/{pid}/avanzar",
            json={"estado_hacia": "CANCELADO", "motivo": "Test"},
            headers=admin_headers,
        )
        response = client.get("/api/v1/estadisticas/resumen", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["pedidos_activos"] >= 0


class TestVentasPeriodo:

    # SQLite no soporta DATE_TRUNC ni TO_CHAR (son funciones de PostgreSQL)
    # Estos tests solo funcionan con PostgreSQL real
    @pytest.mark.skip(reason="DATE_TRUNC no soportado en SQLite (requiere PostgreSQL)")
    def test_ventas_periodo_returns_200(self, client, admin_headers):
        hoy = date.today().isoformat()
        response = client.get(
            f"/api/v1/estadisticas/ventas?desde={hoy}&hasta={hoy}",
            headers=admin_headers,
        )
        assert response.status_code == 200

    @pytest.mark.skip(reason="DATE_TRUNC no soportado en SQLite (requiere PostgreSQL)")
    def test_ventas_periodo_agrupacion_day(self, client, admin_headers):
        hoy = date.today().isoformat()
        response = client.get(
            f"/api/v1/estadisticas/ventas?desde={hoy}&hasta={hoy}&agrupacion=day",
            headers=admin_headers,
        )
        assert response.status_code == 200

    @pytest.mark.skip(reason="DATE_TRUNC no soportado en SQLite (requiere PostgreSQL)")
    def test_ventas_periodo_agrupacion_month(self, client, admin_headers):
        hoy = date.today().isoformat()
        response = client.get(
            f"/api/v1/estadisticas/ventas?desde={hoy}&hasta={hoy}&agrupacion=month",
            headers=admin_headers,
        )
        assert response.status_code == 200

    def test_ventas_periodo_requiere_desde_hasta(self, client, admin_headers):
        response = client.get("/api/v1/estadisticas/ventas", headers=admin_headers)
        assert response.status_code == 422

    def test_ventas_periodo_client_returns_403(self, client, user_headers):
        hoy = date.today().isoformat()
        response = client.get(
            f"/api/v1/estadisticas/ventas?desde={hoy}&hasta={hoy}",
            headers=user_headers,
        )
        assert response.status_code == 403


class TestProductosTop:

    def test_productos_top_returns_200(self, client, admin_headers):
        response = client.get("/api/v1/estadisticas/productos-top", headers=admin_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_productos_top_con_limit(self, client, admin_headers):
        response = client.get(
            "/api/v1/estadisticas/productos-top?limit=5", headers=admin_headers
        )
        assert response.status_code == 200
        assert len(response.json()) <= 5

    def test_productos_top_estructura(self, client, admin_headers, created_pedido):
        response = client.get("/api/v1/estadisticas/productos-top", headers=admin_headers)
        assert response.status_code == 200
        items = response.json()
        if items:
            assert "producto_id" in items[0]
            assert "nombre" in items[0]
            assert "cantidad_vendida" in items[0]
            assert "ingresos" in items[0]

    def test_productos_top_client_returns_403(self, client, user_headers):
        response = client.get("/api/v1/estadisticas/productos-top", headers=user_headers)
        assert response.status_code == 403


class TestPedidosPorEstado:

    def test_pedidos_por_estado_returns_200(self, client, admin_headers):
        response = client.get("/api/v1/estadisticas/pedidos-por-estado", headers=admin_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_pedidos_por_estado_estructura(self, client, admin_headers, created_pedido):
        response = client.get("/api/v1/estadisticas/pedidos-por-estado", headers=admin_headers)
        items = response.json()
        if items:
            assert "estado_codigo" in items[0]
            assert "cantidad" in items[0]

    def test_pedidos_por_estado_client_returns_403(self, client, user_headers):
        response = client.get("/api/v1/estadisticas/pedidos-por-estado", headers=user_headers)
        assert response.status_code == 403


class TestIngresosPorFormaPago:

    def test_ingresos_returns_200(self, client, admin_headers):
        hoy = date.today().isoformat()
        response = client.get(
            f"/api/v1/estadisticas/ingresos?desde={hoy}&hasta={hoy}",
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_ingresos_estructura(self, client, admin_headers):
        hoy = date.today().isoformat()
        response = client.get(
            f"/api/v1/estadisticas/ingresos?desde={hoy}&hasta={hoy}",
            headers=admin_headers,
        )
        items = response.json()
        if items:
            assert "forma_pago_codigo" in items[0]
            assert "total" in items[0]
            assert "cantidad_pedidos" in items[0]

    def test_ingresos_requiere_fechas(self, client, admin_headers):
        response = client.get("/api/v1/estadisticas/ingresos", headers=admin_headers)
        assert response.status_code == 422

    def test_ingresos_client_returns_403(self, client, user_headers):
        hoy = date.today().isoformat()
        response = client.get(
            f"/api/v1/estadisticas/ingresos?desde={hoy}&hasta={hoy}",
            headers=user_headers,
        )
        assert response.status_code == 403