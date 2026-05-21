"""Router para gestión de roles de usuario (solo ADMIN)."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.deps import get_current_active_user, require_role
from app.modules.usuario.usuario_schema import UsuarioAuth
from app.modules.usuario_rol.usuario_rol_schema import UsuarioRolCreate, UsuarioRolRead
from app.modules.usuario_rol.usuario_rol_service import UsuarioRolService
from app.modules.usuario_rol.usuario_rol_uow import UsuarioRolUnitOfWork

usuario_rol_router = APIRouter(prefix="/api/v1/admin/roles", tags=["Admin - Roles"])


def get_service() -> UsuarioRolService:
    return UsuarioRolService(UsuarioRolUnitOfWork())


@usuario_rol_router.post(
    "/asignar",
    response_model=UsuarioRolRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(["ADMIN"]))],
)
def asignar_rol(
    data: UsuarioRolCreate,
    current_user: Annotated[UsuarioAuth, Depends(get_current_active_user)],
    service: UsuarioRolService = Depends(get_service),
):
    # Asigna automáticamente quién hizo la asignación
    data.asignado_por_id = current_user.id
    return service.asignar_rol(data)


@usuario_rol_router.delete(
    "/{usuario_id}/{rol_codigo}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_role(["ADMIN"]))],
)
def revocar_rol(
    usuario_id: int,
    rol_codigo: str,
    service: UsuarioRolService = Depends(get_service),
):
    return service.revocar_rol(usuario_id, rol_codigo)


@usuario_rol_router.get(
    "/usuario/{usuario_id}",
    response_model=list[str],
    dependencies=[Depends(require_role(["ADMIN"]))],
)
def listar_roles_usuario(
    usuario_id: int,
    service: UsuarioRolService = Depends(get_service),
):
    return service.listar_roles_usuario(usuario_id)
