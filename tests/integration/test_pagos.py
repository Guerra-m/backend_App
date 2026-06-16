"""
tests/integration/test_pagos.py
Tests del modulo de pagos (MercadoPago).
Se mockea el SDK de MP para no hacer llamadas reales.
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


class TestCrearPago:
    """POST /api/v1/pagos/crear"""

    def test_crear_pago_exitoso(self, client, user_headers, created_pedido):
        """Crear pago para un pedido existente -> 201."""
        response = client.post(
            "/api/v1/pagos/crear",
            json={
                "pedido_id": created_pedido["id"],
                "transaction_amount": created_pedido["total"],
            },
            headers=user_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["pedido_id"] == created_pedido["id"]
        assert data["mp_status"] == "pending"
        assert "external_reference" in data
        assert "idempotency_key" in data

    def test_crear_pago_sin_auth_returns_401(self, client, created_pedido):
        """Sin auth -> 401."""
        response = client.post(
            "/api/v1/pagos/crear",
            json={"pedido_id": created_pedido["id"], "transaction_amount": 100.0},
        )
        assert response.status_code == 401

    def test_crear_pago_pedido_inexistente_returns_404(self, client, user_headers):
        """Pedido inexistente -> 404."""
        response = client.post(
            "/api/v1/pagos/crear",
            json={"pedido_id": 99999, "transaction_amount": 100.0},
            headers=user_headers,
        )
        assert response.status_code == 404

    def test_crear_pago_duplicado_returns_409(self, client, user_headers, created_pedido):
        """Segundo pago para el mismo pedido -> 409."""
        payload = {
            "pedido_id": created_pedido["id"],
            "transaction_amount": created_pedido["total"],
        }
        # Primer pago
        r1 = client.post("/api/v1/pagos/crear", json=payload, headers=user_headers)
        assert r1.status_code == 201

        # Segundo pago (duplicado)
        r2 = client.post("/api/v1/pagos/crear", json=payload, headers=user_headers)
        assert r2.status_code == 409

    def test_idempotency_key_generado(self, client, user_headers, created_pedido):
        """El pago tiene idempotency_key unico (evita cobros duplicados)."""
        response = client.post(
            "/api/v1/pagos/crear",
            json={
                "pedido_id": created_pedido["id"],
                "transaction_amount": created_pedido["total"],
            },
            headers=user_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["idempotency_key"] is not None
        assert len(data["idempotency_key"]) > 0


class TestObtenerPago:
    """GET /api/v1/pagos/{pedido_id}"""

    def test_obtener_pago_existente(self, client, user_headers, created_pedido):
        """Obtener pago de un pedido con pago registrado."""
        pedido_id = created_pedido["id"]

        # Crear pago primero
        client.post(
            "/api/v1/pagos/crear",
            json={"pedido_id": pedido_id, "transaction_amount": created_pedido["total"]},
            headers=user_headers,
        )

        response = client.get(f"/api/v1/pagos/{pedido_id}", headers=user_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["pedido_id"] == pedido_id

    def test_obtener_pago_sin_pago_returns_404(self, client, user_headers, created_pedido):
        """Pedido sin pago registrado -> 404."""
        response = client.get(
            f"/api/v1/pagos/{created_pedido['id']}", headers=user_headers
        )
        assert response.status_code == 404

    def test_admin_puede_ver_cualquier_pago(
        self, client, admin_headers, user_headers, created_pedido
    ):
        """ADMIN puede ver el pago de cualquier pedido."""
        pedido_id = created_pedido["id"]
        client.post(
            "/api/v1/pagos/crear",
            json={"pedido_id": pedido_id, "transaction_amount": created_pedido["total"]},
            headers=user_headers,
        )
        response = client.get(f"/api/v1/pagos/{pedido_id}", headers=admin_headers)
        assert response.status_code == 200


class TestWebhookMP:
    """POST /api/v1/pagos/webhook"""

    def test_webhook_topic_no_payment_ignorado(self, client):
        """Topic distinto a 'payment' -> ignorado (200 con status ignored)."""
        response = client.post(
            "/api/v1/pagos/webhook",
            json={"type": "merchant_order", "id": "123"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "ignored"

    def test_webhook_sin_payment_id_ignorado(self, client):
        """Sin payment_id -> ignorado."""
        response = client.post(
            "/api/v1/pagos/webhook",
            json={"type": "payment", "data": {}},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "ignored"

    def test_webhook_approved_avanza_pedido(
        self, client, user_headers, created_pedido
    ):
        """Webhook approved -> pedido avanza a CONFIRMADO."""
        pedido_id = created_pedido["id"]

        # Crear pago primero para tener external_reference
        pago_response = client.post(
            "/api/v1/pagos/crear",
            json={"pedido_id": pedido_id, "transaction_amount": created_pedido["total"]},
            headers=user_headers,
        )
        assert pago_response.status_code == 201
        external_reference = pago_response.json()["external_reference"]

        # Mockear la llamada al SDK de MP
        mock_payment_data = {
            "id": 123456,
            "status": "approved",
            "status_detail": "accredited",
            "external_reference": external_reference,
            "transaction_amount": created_pedido["total"],
            "payment_method_id": "visa",
        }

        with patch("mercadopago.SDK") as mock_sdk:
            mock_instance = MagicMock()
            mock_sdk.return_value = mock_instance
            mock_instance.payment.return_value.get.return_value = {
                "status": 200,
                "response": mock_payment_data,
            }

            response = client.post(
                "/api/v1/pagos/webhook",
                json={"type": "payment", "data": {"id": "123456"}},
            )

        assert response.status_code == 200