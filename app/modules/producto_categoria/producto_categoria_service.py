from fastapi import HTTPException, status
from app.modules.producto_categoria.producto_categoria_uow import ProductoCategoriaUnitOfWork
from app.modules.producto_categoria.producto_categoria_schema import (
    ProductoCategoriaCreate, ProductoCategoriaRead
)


class ProductoCategoriaService:
    def __init__(self, uow: ProductoCategoriaUnitOfWork):
        self.uow = uow

    def vincular(self, data: ProductoCategoriaCreate) -> ProductoCategoriaRead:
        with self.uow as uow:
            # Validar que el producto y la categoría existan
            try:
                uow.productos.get_by_id(data.producto_id)
            except ValueError as e:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

            try:
                uow.categorias.get_by_id(data.categoria_id)
            except ValueError as e:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

            try:
                link = uow.producto_categorias.create(data)
            except ValueError as e:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

            return ProductoCategoriaRead.model_validate(link)

    def listar_por_producto(self, producto_id: int) -> list[ProductoCategoriaRead]:
        with self.uow as uow:
            links = uow.producto_categorias.get_by_producto(producto_id)
            return [ProductoCategoriaRead.model_validate(l) for l in links]

    def listar_por_categoria(self, categoria_id: int) -> list[ProductoCategoriaRead]:
        with self.uow as uow:
            links = uow.producto_categorias.get_by_categoria(categoria_id)
            return [ProductoCategoriaRead.model_validate(l) for l in links]

    def desvincular(self, producto_id: int, categoria_id: int) -> dict:
        with self.uow as uow:
            try:
                uow.producto_categorias.delete(producto_id, categoria_id)
            except ValueError as e:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
            return {"mensaje": "Vínculo eliminado correctamente"}
