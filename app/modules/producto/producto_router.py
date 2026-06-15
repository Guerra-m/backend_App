from typing import Annotated, Optional
from fastapi import APIRouter, Query, status, Depends
from pydantic import BaseModel, Field

from app.modules.producto.producto_service import ProductoService
from app.modules.producto.producto_uow import ProductoUnitOfWork
from app.modules.producto.producto_schema import (
    ProductoCreate, ProductoReadConRelaciones, ProductoUpdate, ProductoRead,
    ImagenProductoUpdate)

from app.core.deps import get_current_active_user, require_role
from app.modules.usuario.usuario_schema import UsuarioAuth

producto_router = APIRouter(
    prefix="/api/v1/productos", 
    tags=["Productos"])


def get_producto_service() -> ProductoService:
    return ProductoService(ProductoUnitOfWork())


class DisponibilidadUpdate(BaseModel):
    disponible: bool
    stock_cantidad: Optional[int] = None

class AgregarIngredienteRequest(BaseModel):
    cantidad: float = Field(gt=0, description="Cantidad del ingrediente en el producto")
    unidad_medida_id: int = Field(description="ID de la unidad de medida")
    es_removible: bool = False


# GET ────────────────────────────────────────────────────────────────────

@producto_router.get("/", response_model=list[ProductoReadConRelaciones])
def listar_productos(
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    categoria_id: Annotated[Optional[int], Query(description="Filtrar por categoría")] = None,
    disponible: Annotated[Optional[bool], Query(description="Filtrar por disponibilidad")] = None,
    texto: Annotated[Optional[str], Query(description="Búsqueda por nombre")] = None,
    service: ProductoService = Depends(get_producto_service),
):
    return service.listar_filtrado(
        offset=offset, limit=limit,
        categoria_id=categoria_id, disponible=disponible, texto=texto,
    )


@producto_router.get("/disponibles", response_model=list[ProductoRead])
def listar_disponibles(
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    service: ProductoService = Depends(get_producto_service)
):
    #Lista unicamente productos con disponible=True y stock > 0
    return service.listar_disponibles(offset=offset, limit=limit)


@producto_router.get("/{producto_id}", response_model=ProductoReadConRelaciones)
def obtener_producto(
    producto_id: int,
    service: ProductoService = Depends(get_producto_service)
):
    return service.obtener_producto(producto_id)


# POST ───────────────────────────────────────────────────────────────────

@producto_router.post(
        "/", response_model=ProductoRead, 
        status_code=status.HTTP_201_CREATED, 
        dependencies=[Depends(require_role(["ADMIN"]))]
        )
def crear_producto(
    data: ProductoCreate,
    service: ProductoService = Depends(get_producto_service)
):
    return service.crear_producto(data)


# PUT ────────────────────────────────────────────────────────────────────

@producto_router.put(
        "/{producto_id}", 
        response_model=ProductoRead, 
        dependencies=[Depends(require_role(["ADMIN"]))]
        )
def actualizar_producto(
    producto_id: int,
    data: ProductoUpdate,
    service: ProductoService = Depends(get_producto_service)
):
    return service.actualizar_producto(producto_id, data)



# DELETE ─────────────────────────────────────────────────────────────────

@producto_router.delete(
        "/{producto_id}", 
        status_code=status.HTTP_200_OK, 
        dependencies=[Depends(require_role(["ADMIN"]))]
        )
def eliminar_producto(
    producto_id: int,
    service: ProductoService = Depends(get_producto_service)
):
    #Soft delete
    return service.eliminar_producto(producto_id)

# disponibilidad — ADMIN y STOCK pueden usar esto para activar/desactivar productos y 
# actualizar stock sin tocar otros campos.

@producto_router.patch(
    "/{producto_id}/disponibilidad",
    response_model=ProductoRead,
    dependencies=[Depends(require_role(["ADMIN", "STOCK"]))],
)
def actualizar_disponibilidad(
    producto_id: int,
    data: DisponibilidadUpdate,
    service: ProductoService = Depends(get_producto_service),
):
    """Activa/desactiva un producto y opcionalmente actualiza stock. ADMIN y STOCK."""
    return service.actualizar_disponibilidad(
        producto_id, data.disponible, data.stock_cantidad
    )


# Relaciones: Categorías ─────────────────────────────────────────────────

@producto_router.post(
    "/{producto_id}/categorias/{categoria_id}",
    status_code=status.HTTP_200_OK, 
    dependencies=[Depends(require_role(["ADMIN"]))]
)
def agregar_categoria(
    producto_id: int,
    categoria_id: int,
    es_principal: Annotated[bool, Query(description="¿Es la categoría principal del producto?")] = False,
    service: ProductoService = Depends(get_producto_service)
):
    return service.agregar_categoria(producto_id, categoria_id, es_principal)


@producto_router.delete(
    "/{producto_id}/categorias/{categoria_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_role(["ADMIN"]))],
)
def quitar_categoria(
    producto_id: int,
    categoria_id: int,
    service: ProductoService = Depends(get_producto_service)
):
    return service.quitar_categoria(producto_id, categoria_id)


# Relaciones: Ingredientes ───────────────────────────────────────────────

@producto_router.post(
    "/{producto_id}/ingredientes/{ingrediente_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_role(["ADMIN"]))],
)
def agregar_ingrediente(
    producto_id: int,
    ingrediente_id: int,
    data: AgregarIngredienteRequest,
    service: ProductoService = Depends(get_producto_service)
):
    return service.agregar_ingrediente(
        producto_id, ingrediente_id, 
        data.cantidad, data.unidad_medida_id,data.es_removible)


@producto_router.delete(
    "/{producto_id}/ingredientes/{ingrediente_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_role(["ADMIN"]))],
)
def quitar_ingrediente(
    producto_id: int,
    ingrediente_id: int,
    service: ProductoService = Depends(get_producto_service)
):
    return service.quitar_ingrediente(producto_id, ingrediente_id)


# PATCH imagenes 
 
@producto_router.patch(
    "/{producto_id}/imagenes",
    response_model=ProductoRead,
    dependencies=[Depends(require_role(["ADMIN"]))],
)
def actualizar_imagenes(
    producto_id: int,
    data: ImagenProductoUpdate,
    service: ProductoService = Depends(get_producto_service),
):
    """Reemplaza el array completo de imágenes Cloudinary del producto."""
    return service.actualizar_imagenes(producto_id, data)
 