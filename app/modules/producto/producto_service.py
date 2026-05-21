from fastapi import HTTPException, status
from app.modules.producto.producto_uow import ProductoUnitOfWork
from app.modules.producto.producto_schema import ProductoCreate, ProductoUpdate, ProductoRead
from app.modules.producto_categoria.producto_categoria_schema import ProductoCategoriaCreate
from app.modules.producto_ingrediente.producto_ingrediente_schema import ProductoIngredienteCreate


class ProductoService:
    def __init__(self, uow: ProductoUnitOfWork):
        self.uow = uow

    def crear_producto(self, data: ProductoCreate) -> ProductoRead:
        with self.uow as uow:
            producto = uow.productos.create(data)
            return ProductoRead.model_validate(producto)

    def obtener_producto(self, producto_id: int) -> ProductoRead:
        with self.uow as uow:
            try:
                producto = uow.productos.get_by_id(producto_id)
            except ValueError as e:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
            return ProductoRead.model_validate(producto)

    def listar_productos(self, offset: int = 0, limit: int = 20) -> list[ProductoRead]:
        with self.uow as uow:
            return [
                ProductoRead.model_validate(p)
                for p in uow.productos.get_all(offset=offset, limit=limit)
            ]

    def listar_disponibles(self, offset: int = 0, limit: int = 20) -> list[ProductoRead]:
        
        #Solo devuelve productos con disponible=True y stock > 0. 
        with self.uow as uow:
            return [
                ProductoRead.model_validate(p)
                for p in uow.productos.get_disponibles(offset=offset, limit=limit)
            ]

    def actualizar_producto(self, producto_id: int, data: ProductoUpdate) -> ProductoRead:
        with self.uow as uow:
            try:
                producto = uow.productos.update(producto_id, data)
            except ValueError as e:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
            return ProductoRead.model_validate(producto)

    def eliminar_producto(self, producto_id: int) -> dict:
        with self.uow as uow:
            try:
                uow.productos.soft_delete(producto_id)
            except ValueError as e:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
            return {"mensaje": f"Producto {producto_id} eliminado correctamente"}

    # Relaciones dentro de la misma transacción ──────────────────────────

    def agregar_categoria(self, producto_id: int, categoria_id: int, es_principal: bool = False) -> dict:
        with self.uow as uow:
            # Verificar que ambos existan
            try:
                uow.productos.get_by_id(producto_id)
            except ValueError as e:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

            try:
                uow.producto_categorias.create(
                    ProductoCategoriaCreate(
                        producto_id=producto_id,
                        categoria_id=categoria_id,
                        es_principal=es_principal
                    )
                )
            except ValueError as e:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

            return {"mensaje": "Categoría vinculada al producto correctamente"}

    def quitar_categoria(self, producto_id: int, categoria_id: int) -> dict:
        with self.uow as uow:
            try:
                uow.producto_categorias.delete(producto_id, categoria_id)
            except ValueError as e:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
            return {"mensaje": "Categoría desvinculada del producto correctamente"}

    def agregar_ingrediente(self, producto_id: int, ingrediente_id: int, es_removible: bool = False) -> dict:
        with self.uow as uow:
            try:
                uow.productos.get_by_id(producto_id)
            except ValueError as e:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

            try:
                uow.producto_ingredientes.create(
                    ProductoIngredienteCreate(
                        producto_id=producto_id,
                        ingrediente_id=ingrediente_id,
                        es_removible=es_removible
                    )
                )
            except ValueError as e:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

            return {"mensaje": "Ingrediente vinculado al producto correctamente"}

    def quitar_ingrediente(self, producto_id: int, ingrediente_id: int) -> dict:
        with self.uow as uow:
            try:
                uow.producto_ingredientes.delete(producto_id, ingrediente_id)
            except ValueError as e:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
            return {"mensaje": "Ingrediente desvinculado del producto correctamente"}
