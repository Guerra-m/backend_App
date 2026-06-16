"""
tests/integration/test_middlewares.py
Tests de los middlewares: Logging y Timing.
"""
import uuid
from fastapi.testclient import TestClient


class TestLoggingMiddleware:
    """Verifica que el LoggingMiddleware agrega X-Request-ID."""

    def test_request_id_presente(self, client):
        response = client.get("/health")
        assert "x-request-id" in response.headers

    def test_request_id_es_uuid_v4(self, client):
        response = client.get("/health")
        request_id = response.headers["x-request-id"]
        parsed = uuid.UUID(request_id)
        assert parsed.version == 4

    def test_request_id_unico_por_request(self, client):
        r1 = client.get("/health")
        r2 = client.get("/health")
        assert r1.headers["x-request-id"] != r2.headers["x-request-id"]

    def test_request_id_en_respuesta_de_error(self, client):
        """El request_id aparece en responses de error (correlacion con logs)."""
        response = client.get("/esta-ruta-no-existe")
        assert response.status_code == 404
        assert "x-request-id" in response.headers


class TestTimingMiddleware:
    """Verifica que el TimingMiddleware agrega headers de tiempo."""

    def test_response_time_header_presente(self, client):
        response = client.get("/health")
        assert "x-response-time-ms" in response.headers

    def test_response_time_es_numerico(self, client):
        response = client.get("/health")
        ms = float(response.headers["x-response-time-ms"])
        assert ms >= 0

    def test_response_time_razonable(self, client):
        """El tiempo reportado es razonable (entre 0 y 5000ms)."""
        response = client.get("/health")
        ms = float(response.headers["x-response-time-ms"])
        assert 0 <= ms < 5000

    def test_server_timing_header_presente(self, client):
        response = client.get("/health")
        assert "server-timing" in response.headers
        assert "total" in response.headers["server-timing"]


class TestExceptionHandlers:
    """Verifica formato unificado de errores."""

    def test_404_tiene_formato_unificado(self, client):
        response = client.get("/ruta-inexistente")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "code" in data
        assert "timestamp" in data

    def test_401_tiene_formato_unificado(self, client):
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "code" in data

    def test_422_tiene_formato_unificado(self, client):
        response = client.post("/api/v1/auth/register", json={"email": "no-es-email"})
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert "code" in data

    def test_403_tiene_formato_unificado(self, client, user_headers):
        response = client.get("/api/v1/auth/admin/usuarios", headers=user_headers)
        assert response.status_code == 403
        data = response.json()
        assert "detail" in data
        assert "code" in data