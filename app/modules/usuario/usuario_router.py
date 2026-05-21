"""
Router de autenticación y gestión de usuarios.
Endpoints: register, login, logout, refresh, me, admin routes.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.deps import get_current_active_user, require_role
from app.modules.usuario.usuario_schema import (
    UsuarioCreate,
    UsuarioReadWithRoles,
    UsuarioAuth,
    TokenRefreshRequest,
)
from app.modules.usuario.usuario_service import UsuarioService
from app.modules.usuario.usuario_uow import UsuarioUnitOfWork

usuario_router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


def get_usuario_service() -> UsuarioService:
    return UsuarioService(UsuarioUnitOfWork())


# ─── Registro ─────────────────────────────────────────────────────────────────

@usuario_router.post(
    "/register",
    response_model=UsuarioReadWithRoles,
    status_code=status.HTTP_201_CREATED,
)
def register(
    data: UsuarioCreate,
    service: UsuarioService = Depends(get_usuario_service),
):
    return service.register(data)


# ─── Login (OAuth2 Password Flow — usa email como username) ──────────────────

@usuario_router.post("/token")
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    response: Response,
    service: UsuarioService = Depends(get_usuario_service),
):
    """
    Autentica al usuario. El campo 'username' del form recibe el email.
    Setea access_token en cookie HttpOnly y retorna refresh_token en body.
    """
    result = service.authenticate(form_data.username, form_data.password)

    # Cookie HttpOnly para el access token
    response.set_cookie(
        key="access_token",
        value=result["access_token"],
        httponly=True,
        max_age=result["expires_in"],
        samesite="lax",
        secure=False,  # En producción con HTTPS → True
    )

    return {
        "mensaje": "Login exitoso",
        "refresh_token": result["refresh_token"],
        "expires_in": result["expires_in"],
    }


# ─── Refresh Token ───────────────────────────────────────────────────────────

@usuario_router.post("/refresh")
def refresh_token(
    body: TokenRefreshRequest,
    response: Response,
    service: UsuarioService = Depends(get_usuario_service),
):
    """Renueva el access token usando un refresh token válido."""
    result = service.refresh_access_token(body.refresh_token)

    response.set_cookie(
        key="access_token",
        value=result["access_token"],
        httponly=True,
        max_age=result["expires_in"],
        samesite="lax",
        secure=False,
    )

    return {
        "mensaje": "Token renovado",
        "refresh_token": result["refresh_token"],
        "expires_in": result["expires_in"],
    }


# ─── Logout ──────────────────────────────────────────────────────────────────

@usuario_router.post("/logout")
def logout(
    response: Response,
    current_user: Annotated[UsuarioAuth, Depends(get_current_active_user)],
    service: UsuarioService = Depends(get_usuario_service),
):
    """Revoca todos los refresh tokens y limpia la cookie."""
    service.logout(current_user.id)

    response.delete_cookie(
        key="access_token",
        httponly=True,
        samesite="lax",
        secure=False,
    )
    return {"mensaje": "Sesión cerrada exitosamente"}


# ─── Rutas protegidas ────────────────────────────────────────────────────────

@usuario_router.get("/me", response_model=UsuarioReadWithRoles)
def read_me(
    current_user: Annotated[UsuarioAuth, Depends(get_current_active_user)],
    service: UsuarioService = Depends(get_usuario_service),
):
    return service.obtener_perfil(current_user.id)


# ─── Rutas de administración (RBAC: solo ADMIN) ─────────────────────────────

@usuario_router.get(
    "/admin/usuarios",
    response_model=list[UsuarioReadWithRoles],
    dependencies=[Depends(require_role(["ADMIN"]))],
)
def listar_usuarios(
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    service: UsuarioService = Depends(get_usuario_service),
):
    return service.listar_usuarios(offset=offset, limit=limit)
