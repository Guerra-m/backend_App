"""
Service de Usuario — lógica de negocio para autenticación y gestión.
"""

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status

from app.core.config import settings
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    generate_refresh_token,
    hash_refresh_token,
)
from app.modules.usuario.usuario_uow import UsuarioUnitOfWork
from app.modules.usuario.usuario_model import Usuario
from app.modules.usuario.usuario_schema import (
    UsuarioCreate,
    UsuarioRead,
    UsuarioReadWithRoles,
    Token,
    UsuarioUpdate,
)
from app.modules.usuario_rol.usuario_rol_model import UsuarioRol
from app.modules.refresh_token.refresh_token_model import RefreshToken


class UsuarioService:

    def __init__(self, uow: UsuarioUnitOfWork):
        self.uow = uow

    def register(self, data: UsuarioCreate) -> UsuarioReadWithRoles:
        """Registra un nuevo usuario con rol CLIENT por defecto."""
        with self.uow as uow:
            # Validar email único
            if uow.usuarios.get_by_email(data.email):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="El email ya está registrado",
                )

            # Validar que el rol CLIENT exista
            rol_client = uow.roles.get_by_codigo("CLIENT")
            if not rol_client:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Rol CLIENT no encontrado. Ejecutar seed primero.",
                )

            # Crear usuario
            usuario = Usuario(
                nombre=data.nombre,
                apellido=data.apellido,
                email=data.email,
                celular=data.celular,
                password_hash=hash_password(data.password),
            )
            usuario = uow.usuarios.create(usuario)

            # Asignar rol CLIENT
            usuario_rol = UsuarioRol(
                usuario_id=usuario.id,
                rol_codigo="CLIENT",
            )
            uow.usuario_roles.create(usuario_rol)

            return UsuarioReadWithRoles(
                **UsuarioRead.model_validate(usuario).model_dump(),
                roles=["CLIENT"],
            )

    def authenticate(self, email: str, password: str) -> dict:
        """
        Autentica con email + password.
        Retorna access_token + refresh_token.
        """
        with self.uow as uow:
            usuario = uow.usuarios.get_by_email(email)

            if not usuario or not verify_password(password, usuario.password_hash):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Credenciales incorrectas",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Obtener roles del usuario
            roles = uow.usuario_roles.get_roles_by_usuario(usuario.id)

            # Generar access token (JWT)
            access_token = create_access_token(
                data={"sub": str(usuario.id), "roles": roles}
            )

            # Generar refresh token (opaco → hash SHA-256 en BD)
            raw_refresh = generate_refresh_token()
            refresh_record = RefreshToken(
                usuario_id=usuario.id,
                token_hash=hash_refresh_token(raw_refresh),
                expires_at=datetime.now(timezone.utc)
                + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            )
            uow.refresh_tokens.create(refresh_record)

            return {
                "access_token": access_token,
                "refresh_token": raw_refresh,
                "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            }

    def refresh_access_token(self, raw_refresh_token: str) -> dict:
        """Renueva el access token usando un refresh token válido."""
        with self.uow as uow:
            token_hash = hash_refresh_token(raw_refresh_token)
            refresh_record = uow.refresh_tokens.get_valid_by_hash(token_hash)

            if not refresh_record:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Refresh token inválido o expirado",
                )

            usuario = uow.usuarios.get_by_id(refresh_record.usuario_id)
            if not usuario:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Usuario no encontrado",
                )

            # Revocar el refresh token actual (rotación)
            uow.refresh_tokens.revoke(refresh_record)

            # Obtener roles
            roles = uow.usuario_roles.get_roles_by_usuario(usuario.id)

            # Generar nuevo par de tokens
            new_access = create_access_token(
                data={"sub": str(usuario.id), "roles": roles}
            )
            new_raw_refresh = generate_refresh_token()
            new_refresh_record = RefreshToken(
                usuario_id=usuario.id,
                token_hash=hash_refresh_token(new_raw_refresh),
                expires_at=datetime.now(timezone.utc)
                + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            )
            uow.refresh_tokens.create(new_refresh_record)

            return {
                "access_token": new_access,
                "refresh_token": new_raw_refresh,
                "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            }

    def logout(self, usuario_id: int) -> None:
        """Revoca todos los refresh tokens del usuario (logout seguro)."""
        with self.uow as uow:
            uow.refresh_tokens.revoke_all_by_usuario(usuario_id)

    def listar_usuarios(self, offset: int = 0, limit: int = 20, rol: str | None = None) -> list[UsuarioReadWithRoles]:
        with self.uow as uow:
            usuarios = uow.usuarios.get_all(offset=offset, limit=limit, rol=rol)
            result = []
            for u in usuarios:
                roles = uow.usuario_roles.get_roles_by_usuario(u.id)
                result.append(
                    UsuarioReadWithRoles(
                        **UsuarioRead.model_validate(u).model_dump(),
                        roles=roles,
                    )
                )
            return result

    def actualizar_usuario(self, usuario_id: int, data: UsuarioUpdate) -> UsuarioReadWithRoles:
        with self.uow as uow:
            usuario = uow.usuarios.get_by_id(usuario_id)
            if not usuario:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        
            update_data = data.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(usuario, key, value)
        
            usuario = uow.usuarios.update(usuario)
            roles = uow.usuario_roles.get_roles_by_usuario(usuario.id)
            return UsuarioReadWithRoles(
                **UsuarioRead.model_validate(usuario).model_dump(),
                roles=roles,
            )

    def eliminar_usuario(self, usuario_id: int) -> dict:
        with self.uow as uow:
            try:
                uow.usuarios.soft_delete(usuario_id)
            except ValueError as e:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
            return {"mensaje": f"Usuario {usuario_id} eliminado correctamente"}

    def obtener_perfil(self, usuario_id: int) -> UsuarioReadWithRoles:
        """Obtiene el perfil de un usuario con roles."""
        with self.uow as uow:
            usuario = uow.usuarios.get_by_id(usuario_id)
            if not usuario:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Usuario no encontrado",
                )
            roles = uow.usuario_roles.get_roles_by_usuario(usuario.id)
            return UsuarioReadWithRoles(
                **UsuarioRead.model_validate(usuario).model_dump(),
                roles=roles,
            )
