from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select

from app.core.database import engine
from app.core.security import decode_access_token
from app.modules.usuario.usuario_model import Usuario
from app.modules.usuario.usuario_schema import UsuarioAuth
from app.modules.usuario_rol.usuario_rol_model import UsuarioRol


# ─── OAuth2 con Cookie HttpOnly ──────────────────────────────────────────────

class OAuth2PasswordBearerWithCookie(OAuth2PasswordBearer):
    """Extrae el token JWT exclusivamente de una cookie HttpOnly."""

    async def __call__(self, request: Request) -> str | None:
        token = request.cookies.get("access_token")
        if not token:
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="No autenticado",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return None
        return token


oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl="/api/v1/auth/token")


# ─── Dependencias de autenticación ───────────────────────────────────────────

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> UsuarioAuth:
   
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas o token expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id_str: str | None = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception

    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise credentials_exception

    # Lectura directa en sesión (no necesita transacción UoW)
    with Session(engine) as session:
        usuario = session.get(Usuario, user_id)
        if usuario is None or usuario.deleted_at is not None:
            raise credentials_exception

        # Cargar roles desde la tabla intermedia
        statement = select(UsuarioRol.rol_codigo).where(
            UsuarioRol.usuario_id == user_id,
            # Solo roles vigentes (sin expiración o aún no expirados)
        )
        roles = list(session.exec(statement).all())

        return UsuarioAuth(
            id=usuario.id,
            nombre=usuario.nombre,
            apellido=usuario.apellido,
            email=usuario.email,
            celular=usuario.celular,
            roles=roles,
        )


async def get_current_active_user(
    current_user: Annotated[UsuarioAuth, Depends(get_current_user)],
) -> UsuarioAuth:
    return current_user


def require_role(allowed_roles: list[str]):
   
    async def role_checker(
        current_user: Annotated[UsuarioAuth, Depends(get_current_active_user)],
    ) -> UsuarioAuth:
        # ADMIN tiene acceso total siempre
        if "ADMIN" in current_user.roles:
            return current_user

        if not any(role in allowed_roles for role in current_user.roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Permisos insuficientes. Tus roles: {current_user.roles}. "
                    f"Se requiere uno de: {allowed_roles}"
                ),
            )
        return current_user

    return role_checker
