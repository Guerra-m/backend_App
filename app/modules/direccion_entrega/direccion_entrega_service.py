"""Service de DireccionEntrega — el usuario solo opera sobre sus propias direcciones."""

from fastapi import HTTPException, status

from app.modules.direccion_entrega.direccion_entrega_uow import DireccionEntregaUnitOfWork
from app.modules.direccion_entrega.direccion_entrega_schema import (
    DireccionEntregaCreate,
    DireccionEntregaUpdate,
    DireccionEntregaRead,
)


class DireccionEntregaService:

    def __init__(self, uow: DireccionEntregaUnitOfWork):
        self.uow = uow

    def crear(self, usuario_id: int, data: DireccionEntregaCreate) -> DireccionEntregaRead:
        with self.uow as uow:
            direccion = uow.direcciones.create(usuario_id, data)
            return DireccionEntregaRead.model_validate(direccion)

    def listar_mis_direcciones(self, usuario_id: int) -> list[DireccionEntregaRead]:
        with self.uow as uow:
            direcciones = uow.direcciones.get_by_usuario(usuario_id)
            return [DireccionEntregaRead.model_validate(d) for d in direcciones]

    def actualizar(
        self, usuario_id: int, direccion_id: int, data: DireccionEntregaUpdate
    ) -> DireccionEntregaRead:
        with self.uow as uow:
            direccion = uow.direcciones.get_by_id(direccion_id)
            if not direccion or direccion.usuario_id != usuario_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dirección no encontrada",
                )
            direccion = uow.direcciones.update(direccion, data)
            return DireccionEntregaRead.model_validate(direccion)

    def eliminar(self, usuario_id: int, direccion_id: int) -> dict:
        with self.uow as uow:
            direccion = uow.direcciones.get_by_id(direccion_id)
            if not direccion or direccion.usuario_id != usuario_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dirección no encontrada",
                )
            uow.direcciones.soft_delete(direccion)
            return {"mensaje": f"Dirección {direccion_id} eliminada correctamente"}
