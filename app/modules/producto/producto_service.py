from fastapi import HTTPException, status
from app.modules.categoria.categoria_schema import CategoriaRead
from app.modules.ingrediente.ingrediente_schema import IngredienteRead
from app.modules.producto.producto_uow import ProductoUnitOfWork
from app.modules.producto.producto_schema import ImagenProductoUpdate, ProductoCreate, ProductoReadConRelaciones, ProductoUpdate, ProductoRead, ImagenProductoUpdate
from app.modules.producto_categoria.producto_categoria_schema import ProductoCategoriaCreate
from app.modules.producto_ingrediente.producto_ingrediente_schema import ProductoIngredienteCreate
from app.modules.unidad_medida.unidad_medida_schema import UnidadMedidaRead


class ProductoService:
    def __init__(self, uow: ProductoUnitOfWork):
        self.uow = uow

    def crear_producto(self, data: ProductoCreate) -> ProductoRead:
        with self.uow as uow:
            # Validar unidad_venta_id si se envía
            if data.unidad_venta_id is not None:
                try:
                    uow.unidades.get_by_id(data.unidad_venta_id)
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"UnidadMedida con id {data.unidad_venta_id} no encontrada",
                    )
            producto = uow.productos.create(data)
            return ProductoRead.model_validate(producto)

    def obtener_producto(self, producto_id: int) -> ProductoReadConRelaciones:
        with self.uow as uow:
            try:
                producto = uow.productos.get_by_id(producto_id)
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))
            
            categorias = [
                CategoriaRead.model_validate(link.categoria)
                for link in producto.categorias_link
                if link.categoria and link.categoria.deleted_at is None
            ]
            ingredientes = [
                IngredienteRead.model_validate(link.ingrediente)
                for link in producto.ingredientes_link
                if link.ingrediente
            ]
            unidad_venta = (
                UnidadMedidaRead.model_validate(producto.unidad_venta)
                if producto.unidad_venta else None
            )
            
            result = ProductoReadConRelaciones.model_validate(producto)
            result.categorias = categorias
            result.ingredientes = ingredientes
            result.unidad_venta = unidad_venta
            return result

    def listar_productos(self, offset: int = 0, limit: int = 20) -> list[ProductoRead]:
        with self.uow as uow:
            return [
                ProductoRead.model_validate(p)
                for p in uow.productos.get_all(offset=offset, limit=limit)
            ]
        
    def listar_filtrado(self, offset=0, limit=20, categoria_id=None, disponible=None, texto=None) -> list[ProductoReadConRelaciones]:
        with self.uow as uow:
            productos = uow.productos.get_all_filtrado(
                offset=offset, limit=limit,
                categoria_id=categoria_id,
                disponible=disponible,
                texto=texto,
            )
            result = []
            for producto in productos:
                categorias = [
                    CategoriaRead.model_validate(link.categoria)
                    for link in producto.categorias_link
                    if link.categoria and link.categoria.deleted_at is None
                ]
                ingredientes = [
                    IngredienteRead.model_validate(link.ingrediente)
                    for link in producto.ingredientes_link
                    if link.ingrediente
                ]
                unidad_venta = (
                    UnidadMedidaRead.model_validate(producto.unidad_venta)
                    if producto.unidad_venta else None
                )
                p = ProductoReadConRelaciones.model_validate(producto)
                p.categorias = categorias
                p.ingredientes = ingredientes
                p.unidad_venta = unidad_venta
                result.append(p)
            return result

    def listar_disponibles(self, offset: int = 0, limit: int = 20) -> list[ProductoRead]:
        
        #Solo devuelve productos con disponible=True y stock > 0. 
        with self.uow as uow:
            return [
                ProductoRead.model_validate(p)
                for p in uow.productos.get_disponibles(offset=offset, limit=limit)
            ]

    def actualizar_producto(self, producto_id: int, data: ProductoUpdate) -> ProductoRead:
        with self.uow as uow:
            # Validar unidad_venta_id si se envía
            if data.unidad_venta_id is not None:
                try:
                    uow.unidades.get_by_id(data.unidad_venta_id)
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"UnidadMedida con id {data.unidad_venta_id} no encontrada",
                    )
            try:
                producto = uow.productos.update(producto_id, data)
            except ValueError as e:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
            return ProductoRead.model_validate(producto)
        
    def actualizar_disponibilidad(
        self, producto_id: int, disponible: bool, stock_cantidad: int | None = None
    ) -> ProductoRead:
        """PATCH /disponibilidad — exclusivo de ADMIN y STOCK."""
        with self.uow as uow:
            try:
                producto = uow.productos.actualizar_disponibilidad(
                    producto_id, disponible, stock_cantidad
                )
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
        
    def actualizar_imagenes(self, producto_id: int, data: ImagenProductoUpdate) -> ProductoRead:
        #PATCH /productos/{id}/imagenes — reemplaza el array de URLs
        with self.uow as uow:
            try:
                producto = uow.productos.actualizar_imagenes(producto_id, data.imagenes_url)
            except ValueError as e:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
            return ProductoRead.model_validate(producto)

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

    def agregar_ingrediente(
        self,
        producto_id: int,
        ingrediente_id: int,
        cantidad: float,
        unidad_medida_id: int,
        es_removible: bool = False,
    ) -> dict:
        with self.uow as uow:
            try:
                uow.productos.get_by_id(producto_id)
            except ValueError as e:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

            # Validar unidad_medida_id
            try:
                uow.unidades.get_by_id(unidad_medida_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"UnidadMedida con id {unidad_medida_id} no encontrada",
                )

            try:
                uow.producto_ingredientes.create(
                    ProductoIngredienteCreate(
                        producto_id=producto_id,
                        ingrediente_id=ingrediente_id,
                        cantidad=cantidad,
                        unidad_medida_id=unidad_medida_id,
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
