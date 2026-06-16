"""
tests/integration/test_productos.py
Tests del CRUD de productos.
"""
import pytest
from fastapi.testclient import TestClient


class TestCrearProducto:

    def test_crear_producto_exitoso(self, client, admin_headers, producto_payload):
        response = client.post("/api/v1/productos/", json=producto_payload, headers=admin_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["nombre"] == producto_payload["nombre"]
        assert data["precio_base"] == producto_payload["precio_base"]
        assert data["id"] is not None

    def test_crear_sin_auth_returns_401(self, client, producto_payload):
        response = client.post("/api/v1/productos/", json=producto_payload)
        assert response.status_code == 401

    def test_crear_con_rol_client_returns_403(self, client, user_headers, producto_payload):
        response = client.post("/api/v1/productos/", json=producto_payload, headers=user_headers)
        assert response.status_code == 403

    def test_crear_precio_negativo_returns_422(self, client, admin_headers):
        response = client.post(
            "/api/v1/productos/",
            json={"nombre": "Test", "precio_base": -1.0, "stock_cantidad": 5},
            headers=admin_headers,
        )
        assert response.status_code == 422

    def test_crear_stock_negativo_returns_422(self, client, admin_headers):
        response = client.post(
            "/api/v1/productos/",
            json={"nombre": "Test", "precio_base": 100.0, "stock_cantidad": -1},
            headers=admin_headers,
        )
        assert response.status_code == 422


class TestListarProductos:

    def test_listar_productos_publico(self, client, created_producto):
        response = client.get("/api/v1/productos/")
        assert response.status_code == 200
        ids = [p["id"] for p in response.json()]
        assert created_producto["id"] in ids

    def test_listar_disponibles(self, client, created_producto):
        response = client.get("/api/v1/productos/disponibles")
        assert response.status_code == 200
        items = response.json()
        assert all(p["disponible"] for p in items)

    def test_filtrar_por_texto(self, client, created_producto):
        nombre = created_producto["nombre"]
        response = client.get(f"/api/v1/productos/?texto={nombre[:5]}")
        assert response.status_code == 200
        assert any(p["id"] == created_producto["id"] for p in response.json())


class TestObtenerProducto:

    def test_obtener_por_id_returns_200(self, client, created_producto):
        pid = created_producto["id"]
        response = client.get(f"/api/v1/productos/{pid}")
        assert response.status_code == 200
        assert response.json()["id"] == pid

    def test_obtener_inexistente_returns_404(self, client):
        response = client.get("/api/v1/productos/999999")
        assert response.status_code == 404


class TestActualizarProducto:

    def test_actualizar_precio(self, client, admin_headers, created_producto):
        pid = created_producto["id"]
        response = client.put(
            f"/api/v1/productos/{pid}",
            json={"precio_base": 2000.0},
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["precio_base"] == 2000.0

    def test_actualizar_inexistente_returns_404(self, client, admin_headers):
        response = client.put(
            "/api/v1/productos/999999",
            json={"precio_base": 100.0},
            headers=admin_headers,
        )
        assert response.status_code == 404


class TestDisponibilidad:

    def test_patch_disponibilidad_admin(self, client, admin_headers, created_producto):
        pid = created_producto["id"]
        response = client.patch(
            f"/api/v1/productos/{pid}/disponibilidad",
            json={"disponible": False},
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["disponible"] is False

    def test_patch_disponibilidad_stock(self, client, admin_headers, created_producto):
        pid = created_producto["id"]
        response = client.patch(
            f"/api/v1/productos/{pid}/disponibilidad",
            json={"disponible": True, "stock_cantidad": 50},
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["stock_cantidad"] == 50


class TestEliminarProducto:

    def test_soft_delete_admin(self, client, admin_headers, created_producto):
        pid = created_producto["id"]
        response = client.delete(f"/api/v1/productos/{pid}", headers=admin_headers)
        assert response.status_code == 200

    def test_client_no_puede_eliminar(self, client, user_headers, created_producto):
        pid = created_producto["id"]
        response = client.delete(f"/api/v1/productos/{pid}", headers=user_headers)
        assert response.status_code == 403