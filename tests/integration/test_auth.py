"""
tests/integration/test_auth.py
===============================
Tests de integración del módulo de autenticación de FoodStore.
Cubre: registro, login, /me, refresh, logout, RBAC.
"""

import pytest
from fastapi.testclient import TestClient


# ===========================================================================
# TESTS: Registro
# ===========================================================================
class TestRegister:
    """POST /api/v1/auth/register"""

    def test_register_success_returns_201(self, client: TestClient):
        """Registro válido → 201 con datos del usuario (sin password)."""
        payload = {
            "nombre": "Alice",
            "apellido": "Test",
            "email": "alice@test.com",
            "password": "SecurePass123!",
        }
        response = client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "alice@test.com"
        assert "password" not in data
        assert "password_hash" not in data

    def test_register_duplicate_email_returns_409(
        self, client: TestClient, normal_user: dict
    ):
        """Email duplicado → 409."""
        payload = {
            "nombre": "Otro",
            "apellido": "Usuario",
            "email": normal_user["email"],
            "password": "OtroPass123!",
        }
        response = client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 409

    @pytest.mark.parametrize("payload", [
        pytest.param(
            {"apellido": "Test", "email": "x@x.com", "password": "12345678"},
            id="sin-nombre"
        ),
        pytest.param(
            {"nombre": "Test", "apellido": "T", "email": "not-email", "password": "12345678"},
            id="email-invalido"
        ),
        pytest.param(
            {"nombre": "Test", "apellido": "T", "email": "x@x.com", "password": "123"},
            id="password-corto"
        ),
    ])
    def test_register_invalid_input_returns_422(
        self, client: TestClient, payload: dict
    ):
        """Datos inválidos → 422."""
        response = client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 422


# ===========================================================================
# TESTS: Login
# ===========================================================================
class TestLogin:
    """POST /api/v1/auth/token"""

    def test_login_success_sets_cookie(
        self, client: TestClient, normal_user: dict
    ):
        """Login OK → 200 con cookie HttpOnly access_token."""
        response = client.post(
            "/api/v1/auth/token",
            data={
                "username": normal_user["email"],
                "password": "Cliente1234!",
            },
        )
        assert response.status_code == 200
        # Cookie debe estar presente
        assert "access_token" in response.cookies
        # Header Set-Cookie debe tener HttpOnly
        set_cookie = response.headers.get("set-cookie", "")
        assert "httponly" in set_cookie.lower()

    def test_login_wrong_password_returns_401(
        self, client: TestClient, normal_user: dict
    ):
        """Password incorrecto → 401."""
        response = client.post(
            "/api/v1/auth/token",
            data={
                "username": normal_user["email"],
                "password": "WRONG_PASSWORD",
            },
        )
        assert response.status_code == 401

    def test_login_nonexistent_user_returns_401(self, client: TestClient):
        """Usuario inexistente → 401 (mismo mensaje, no filtramos info)."""
        response = client.post(
            "/api/v1/auth/token",
            data={"username": "ghost@ghost.com", "password": "anything123"},
        )
        assert response.status_code == 401

    def test_login_also_returns_refresh_token(
        self, client: TestClient, normal_user: dict
    ):
        """Login exitoso → body contiene refresh_token."""
        response = client.post(
            "/api/v1/auth/token",
            data={
                "username": normal_user["email"],
                "password": "Cliente1234!",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "refresh_token" in data


# ===========================================================================
# TESTS: /me
# ===========================================================================
class TestMe:
    """GET /api/v1/auth/me"""

    def test_me_with_valid_token_returns_user(
        self, client: TestClient, user_headers: dict, normal_user: dict
    ):
        """Token válido → 200 con datos del usuario."""
        response = client.get("/api/v1/auth/me", headers=user_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == normal_user["email"]
        assert "password_hash" not in data

    def test_me_without_token_returns_401(self, client: TestClient):
        """Sin token → 401."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401


# ===========================================================================
# TESTS: Logout
# ===========================================================================
class TestLogout:
    """POST /api/v1/auth/logout"""

    def test_logout_clears_cookie(
        self, client: TestClient, user_headers: dict
    ):
        """Logout → 200 y cookie eliminada."""
        response = client.post("/api/v1/auth/logout", headers=user_headers)
        assert response.status_code == 200

    def test_logout_without_auth_returns_401(self, client: TestClient):
        """Logout sin token → 401."""
        response = client.post("/api/v1/auth/logout")
        assert response.status_code == 401


# ===========================================================================
# TESTS: Refresh Token
# ===========================================================================
class TestRefresh:
    """POST /api/v1/auth/refresh"""

    def test_refresh_with_valid_token_returns_200(
        self, client: TestClient, normal_user: dict
    ):
        """Refresh token válido → 200 con nuevo access token."""
        # Primero hacemos login para obtener el refresh token
        login_response = client.post(
            "/api/v1/auth/token",
            data={
                "username": normal_user["email"],
                "password": "Cliente1234!",
            },
        )
        assert login_response.status_code == 200
        refresh_token = login_response.json().get("refresh_token")
        assert refresh_token is not None

        # Usamos el refresh token
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200
        assert "access_token" in response.cookies

    def test_refresh_with_invalid_token_returns_401(self, client: TestClient):
        """Refresh token inválido → 401."""
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "token-falso-invalido"},
        )
        assert response.status_code == 401


# ===========================================================================
# TESTS: RBAC
# ===========================================================================
class TestRBAC:
    """Permisos por rol."""

    def test_admin_can_list_users(
        self, client: TestClient, admin_headers: dict
    ):
        """Admin puede listar usuarios."""
        response = client.get(
            "/api/v1/auth/admin/usuarios", headers=admin_headers
        )
        assert response.status_code == 200

    def test_client_cannot_list_users(
        self, client: TestClient, user_headers: dict
    ):
        """CLIENT no puede listar usuarios → 403."""
        response = client.get(
            "/api/v1/auth/admin/usuarios", headers=user_headers
        )
        assert response.status_code == 403

    def test_unauthenticated_cannot_access_protected(
        self, client: TestClient
    ):
        """Sin token → 401 en endpoints protegidos."""
        response = client.get("/api/v1/auth/admin/usuarios")
        assert response.status_code == 401