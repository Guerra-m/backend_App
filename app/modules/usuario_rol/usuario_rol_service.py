"""Service para asignar/revocar roles a usuarios (operación de ADMIN)."""

from fastapi import HTTPException, status

from app.modules.usuario_rol.usuario_rol_uow import UsuarioRolUnitOfWork
from app.modules.usuario_rol.usuario_rol_model import UsuarioRol
from app.modules.usuario_rol.usuario_rol_schema import UsuarioRolCreate, UsuarioRolRead


class UsuarioRolService:

    def __init__(self, uow: UsuarioRolUnitOfWork):
        self.uow = uow

    def asignar_rol(self, data: UsuarioRolCreate) -> UsuarioRolRead:
        with self.uow as uow:
            # Validar que el usuario exista
            if not uow.usuarios.get_by_id(data.usuario_id):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Usuario con id {data.usuario_id} no encontrado",
                )
            # Validar que el rol exista
            if not uow.roles.get_by_codigo(data.rol_codigo):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Rol '{data.rol_codigo}' no encontrado",
                )
            # Validar que no esté ya asignado
            if uow.usuario_roles.get_by_pk(data.usuario_id, data.rol_codigo):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"El usuario ya tiene el rol '{data.rol_codigo}'",
                )

            link = UsuarioRol(
                usuario_id=data.usuario_id,
                rol_codigo=data.rol_codigo,
                asignado_por_id=data.asignado_por_id,
                expires_at=data.expires_at,
            )
            uow.usuario_roles.create(link)
            return UsuarioRolRead.model_validate(link)

    def revocar_rol(self, usuario_id: int, rol_codigo: str) -> dict:
        with self.uow as uow:
            try:
                uow.usuario_roles.delete(usuario_id, rol_codigo)
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=str(e),
                )
            return {"mensaje": f"Rol '{rol_codigo}' revocado del usuario {usuario_id}"}

    def listar_roles_usuario(self, usuario_id: int) -> list[str]:
        with self.uow as uow:
            return uow.usuario_roles.get_roles_by_usuario(usuario_id)
