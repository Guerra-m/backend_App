"""
tests/integration/test_uploads.py
Tests del modulo de uploads (Cloudinary).
Se mockea cloudinary para no hacer llamadas reales.
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import io


MOCK_CLOUDINARY_RESPONSE = {
    "secure_url": "https://res.cloudinary.com/test/image/upload/test.jpg",
    "public_id": "foodstore/productos/test123",
    "width": 800,
    "height": 600,
    "format": "jpg",
    "resource_type": "image",
}


class TestSubirImagen:
    """POST /api/v1/uploads/imagen"""

    def test_subir_imagen_exitoso(self, client, admin_headers):
        """Upload valido con mock de Cloudinary -> 201."""
        with patch("cloudinary.uploader.upload", return_value=MOCK_CLOUDINARY_RESPONSE):
            fake_image = io.BytesIO(b"fake image content")
            response = client.post(
                "/api/v1/uploads/imagen",
                files={"file": ("test.jpg", fake_image, "image/jpeg")},
                data={"folder": "foodstore/productos"},
                headers=admin_headers,
            )
        assert response.status_code == 201
        data = response.json()
        assert "secure_url" in data
        assert "public_id" in data
        assert data["secure_url"] == MOCK_CLOUDINARY_RESPONSE["secure_url"]

    def test_subir_imagen_sin_auth_returns_401(self, client):
        """Sin auth -> 401."""
        fake_image = io.BytesIO(b"fake image content")
        response = client.post(
            "/api/v1/uploads/imagen",
            files={"file": ("test.jpg", fake_image, "image/jpeg")},
        )
        assert response.status_code == 401

    def test_subir_imagen_client_returns_403(self, client, user_headers):
        """CLIENT no puede subir imagenes -> 403."""
        fake_image = io.BytesIO(b"fake image content")
        response = client.post(
            "/api/v1/uploads/imagen",
            files={"file": ("test.jpg", fake_image, "image/jpeg")},
            headers=user_headers,
        )
        assert response.status_code == 403

    def test_subir_imagen_mime_invalido_returns_400(self, client, admin_headers):
        """Tipo MIME no permitido -> 400."""
        with patch("cloudinary.uploader.upload", return_value=MOCK_CLOUDINARY_RESPONSE):
            fake_file = io.BytesIO(b"fake pdf content")
            response = client.post(
                "/api/v1/uploads/imagen",
                files={"file": ("documento.pdf", fake_file, "application/pdf")},
                headers=admin_headers,
            )
        assert response.status_code == 400

    def test_subir_imagen_muy_grande_returns_400(self, client, admin_headers):
        """Imagen mayor a 5MB -> 400."""
        with patch("cloudinary.uploader.upload", return_value=MOCK_CLOUDINARY_RESPONSE):
            # Crear un archivo de mas de 5MB
            large_content = b"x" * (5 * 1024 * 1024 + 1)
            fake_image = io.BytesIO(large_content)
            response = client.post(
                "/api/v1/uploads/imagen",
                files={"file": ("large.jpg", fake_image, "image/jpeg")},
                headers=admin_headers,
            )
        assert response.status_code == 400


class TestEliminarImagen:
    """DELETE /api/v1/uploads/imagen/{public_id}"""

    def test_eliminar_imagen_exitoso(self, client, admin_headers):
        """Eliminar imagen existente en Cloudinary -> 204."""
        with patch(
            "cloudinary.uploader.destroy",
            return_value={"result": "ok"}
        ):
            response = client.delete(
                "/api/v1/uploads/imagen/foodstore/productos/test123",
                headers=admin_headers,
            )
        assert response.status_code == 204

    def test_eliminar_imagen_sin_auth_returns_401(self, client):
        """Sin auth -> 401."""
        response = client.delete("/api/v1/uploads/imagen/foodstore/test123")
        assert response.status_code == 401

    def test_eliminar_imagen_client_returns_403(self, client, user_headers):
        """CLIENT no puede eliminar imagenes -> 403."""
        response = client.delete(
            "/api/v1/uploads/imagen/foodstore/test123",
            headers=user_headers,
        )
        assert response.status_code == 403