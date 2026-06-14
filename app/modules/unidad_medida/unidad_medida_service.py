from fastapi import HTTPException, status
from app.modules.unidad_medida.unidad_medida_uow import UnidadMedidaUnitOfWork
from app.modules.unidad_medida.unidad_medida_schema import (
    UnidadMedidaCreate, UnidadMedidaUpdate, UnidadMedidaRead
)


class UnidadMedidaService:

    def __init__(self, uow: UnidadMedidaUnitOfWork):
        self.uow = uow

    def crear(self, data: UnidadMedidaCreate) -> UnidadMedidaRead:
        with self.uow as uow:
            unidad = uow.unidades.create(data)
            return UnidadMedidaRead.model_validate(unidad)

    def obtener(self, unidad_id: int) -> UnidadMedidaRead:
        with self.uow as uow:
            try:
                unidad = uow.unidades.get_by_id(unidad_id)
            except ValueError as e:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
            return UnidadMedidaRead.model_validate(unidad)

    def listar(self, offset: int = 0, limit: int = 20) -> list[UnidadMedidaRead]:
        with self.uow as uow:
            return [
                UnidadMedidaRead.model_validate(u)
                for u in uow.unidades.get_all(offset=offset, limit=limit)
            ]

    def listar_por_tipo(self, tipo: str) -> list[UnidadMedidaRead]:
        with self.uow as uow:
            return [
                UnidadMedidaRead.model_validate(u)
                for u in uow.unidades.get_by_tipo(tipo)
            ]

    def actualizar(self, unidad_id: int, data: UnidadMedidaUpdate) -> UnidadMedidaRead:
        with self.uow as uow:
            try:
                unidad = uow.unidades.update(unidad_id, data)
            except ValueError as e:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
            return UnidadMedidaRead.model_validate(unidad)

    def eliminar(self, unidad_id: int) -> dict:
        with self.uow as uow:
            try:
                uow.unidades.delete(unidad_id)
            except ValueError as e:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
            return {"mensaje": f"UnidadMedida {unidad_id} eliminada correctamente"}