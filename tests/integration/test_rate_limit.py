"""
tests/integration/test_rate_limit.py
Tests del RateLimitMiddleware de FoodStore.
"""
import pytest
from fastapi.testclient import TestClient
from app.core.rate_limit.rate_limit_middleware import RateLimitMiddleware


class TestRateLimitDefault:
    """Tests del limiter por defecto."""

    def test_headers_ratelimit_presentes(self, client):
        """Toda response trae headers X-RateLimit-*."""
        response = client.get("/api/v1/productos/")
        assert "x-ratelimit-limit" in response.headers
        assert "x-ratelimit-remaining" in response.headers

    def test_429_al_agotar_burst(self, client):
        """Agotar la rafaga inicial -> 429."""
        statuses = []
        for _ in range(20):
            r = client.get("/api/v1/productos/")
            statuses.append(r.status_code)
        assert 429 in statuses

    def test_429_incluye_retry_after(self, client):
        """Respuesta 429 incluye header Retry-After."""
        for _ in range(20):
            client.get("/api/v1/productos/")
        r = client.get("/api/v1/productos/")
        if r.status_code == 429:
            assert "retry-after" in r.headers
            assert int(r.headers["retry-after"]) > 0

    def test_health_excluido_del_rate_limit(self, client):
        """El endpoint /health no tiene rate limit."""
        for _ in range(30):
            r = client.get("/health")
            assert r.status_code == 200


class TestRateLimitAuth:
    """Tests del limiter de auth (mas estricto)."""

    def test_auth_endpoint_se_limita_antes(self, client):
        """El endpoint de auth se rate-limita con capacidad menor."""
        statuses = []
        for _ in range(15):
            r = client.post(
                "/api/v1/auth/token",
                data={"username": "nadie@nadie.com", "password": "wrong"},
            )
            statuses.append(r.status_code)
        assert 429 in statuses

    def test_429_en_register(self, client):
        """El endpoint de register tambien tiene rate limit estricto."""
        statuses = []
        for i in range(15):
            r = client.post(
                "/api/v1/auth/register",
                json={
                    "nombre": f"User{i}",
                    "apellido": "Test",
                    "email": f"user{i}@test.com",
                    "password": "Password123!",
                },
            )
            statuses.append(r.status_code)
        assert 429 in statuses