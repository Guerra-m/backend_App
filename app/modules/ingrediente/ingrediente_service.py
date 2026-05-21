from fastapi import HTTPException, status
from app.modules.ingrediente.ingrediente_uow import IngredienteUnitOfWork
from app.modules.ingrediente.ingrediente_schema import (
    IngredienteCreate, IngredienteUpdate, IngredienteRead
)


class IngredienteService:
    def __init__(self, uow: IngredienteUnitOfWork):
        self.uow = uow

    def crear_ingrediente(self, data: IngredienteCreate) -> IngredienteRead:
        with self.uow as uow:
            ingrediente = uow.ingredientes.create(data)
            return IngredienteRead.model_validate(ingrediente)

    def obtener_ingrediente(self, ingrediente_id: int) -> IngredienteRead:
        with self.uow as uow:
            try:
                ingrediente = uow.ingredientes.get_by_id(ingrediente_id)
            except ValueError as e:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
            return IngredienteRead.model_validate(ingrediente)

    def listar_ingredientes(self, offset: int = 0, limit: int = 20) -> list[IngredienteRead]:
        with self.uow as uow:
            return [
                IngredienteRead.model_validate(i)
                for i in uow.ingredientes.get_all(offset=offset, limit=limit)
            ]

    def listar_alergenos(self) -> list[IngredienteRead]:
        with self.uow as uow:
            return [
                IngredienteRead.model_validate(i)
                for i in uow.ingredientes.get_alergenos()
            ]

    def actualizar_ingrediente(self, ingrediente_id: int, data: IngredienteUpdate) -> IngredienteRead:
        with self.uow as uow:
            try:
                ingrediente = uow.ingredientes.update(ingrediente_id, data)
            except ValueError as e:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
            return IngredienteRead.model_validate(ingrediente)

    def eliminar_ingrediente(self, ingrediente_id: int) -> dict:
        with self.uow as uow:
            try:
                uow.ingredientes.delete(ingrediente_id)
            except ValueError as e:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
            return {"mensaje": f"Ingrediente {ingrediente_id} eliminado correctamente"}
