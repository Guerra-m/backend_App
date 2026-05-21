from fastapi import HTTPException, status
from app.modules.producto_ingrediente.producto_ingrediente_uow import ProductoIngredienteUnitOfWork
from app.modules.producto_ingrediente.producto_ingrediente_schema import (
    ProductoIngredienteCreate, ProductoIngredienteRead
)


class ProductoIngredienteService:
    def __init__(self, uow: ProductoIngredienteUnitOfWork):
        self.uow = uow

    def vincular(self, data: ProductoIngredienteCreate) -> ProductoIngredienteRead:
        with self.uow as uow:
            try:
                uow.productos.get_by_id(data.producto_id)
            except ValueError as e:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

            try:
                uow.ingredientes.get_by_id(data.ingrediente_id)
            except ValueError as e:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

            try:
                link = uow.producto_ingredientes.create(data)
            except ValueError as e:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

            return ProductoIngredienteRead.model_validate(link)

    def listar_por_producto(self, producto_id: int) -> list[ProductoIngredienteRead]:
        with self.uow as uow:
            links = uow.producto_ingredientes.get_by_producto(producto_id)
            return [ProductoIngredienteRead.model_validate(l) for l in links]

    def listar_por_ingrediente(self, ingrediente_id: int) -> list[ProductoIngredienteRead]:
        with self.uow as uow:
            links = uow.producto_ingredientes.get_by_ingrediente(ingrediente_id)
            return [ProductoIngredienteRead.model_validate(l) for l in links]

    def desvincular(self, producto_id: int, ingrediente_id: int) -> dict:
        with self.uow as uow:
            try:
                uow.producto_ingredientes.delete(producto_id, ingrediente_id)
            except ValueError as e:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
            return {"mensaje": "Vínculo eliminado correctamente"}
