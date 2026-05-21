from typing import Annotated
from fastapi import APIRouter, Query, status, Depends
from app.modules.producto.producto_service import ProductoService
from app.modules.producto.producto_uow import ProductoUnitOfWork
from app.modules.producto.producto_schema import ProductoCreate, ProductoUpdate, ProductoRead

from app.core.deps import get_current_active_user, require_role
from app.modules.usuario.usuario_schema import UsuarioAuth

producto_router = APIRouter(prefix="/productos", tags=["Productos"])


def get_producto_service() -> ProductoService:
    return ProductoService(ProductoUnitOfWork())


# GET ────────────────────────────────────────────────────────────────────

@producto_router.get("/", response_model=list[ProductoRead])
def listar_productos(
    _user: Annotated[UsuarioAuth, Depends(get_current_active_user)],
    offset: Annotated[int, Query(ge=0, description="Registros a omitir")] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    service: ProductoService = Depends(get_producto_service)
):
    #Lista todos los productos no eliminados con paginación
    return service.listar_productos(offset=offset, limit=limit)


@producto_router.get("/disponibles", response_model=list[ProductoRead])
def listar_disponibles(
    _user: Annotated[UsuarioAuth, Depends(get_current_active_user)],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    service: ProductoService = Depends(get_producto_service)
):
    #Lista unicamente productos con disponible=True y stock > 0
    return service.listar_disponibles(offset=offset, limit=limit)


@producto_router.get("/{producto_id}", response_model=ProductoRead)
def obtener_producto(
    producto_id: int,
    _user: Annotated[UsuarioAuth, Depends(get_current_active_user)],
    service: ProductoService = Depends(get_producto_service)
):
    return service.obtener_producto(producto_id)


# POST ───────────────────────────────────────────────────────────────────

@producto_router.post("/", response_model=ProductoRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role(["ADMIN", "STOCK"]))])
def crear_producto(
    data: ProductoCreate,
    service: ProductoService = Depends(get_producto_service)
):
    return service.crear_producto(data)


# PUT ────────────────────────────────────────────────────────────────────

@producto_router.put("/{producto_id}", response_model=ProductoRead, dependencies=[Depends(require_role(["ADMIN", "STOCK"]))])
def actualizar_producto(
    producto_id: int,
    data: ProductoUpdate,
    service: ProductoService = Depends(get_producto_service)
):
    return service.actualizar_producto(producto_id, data)


# DELETE ─────────────────────────────────────────────────────────────────

@producto_router.delete("/{producto_id}", status_code=status.HTTP_200_OK, dependencies=[Depends(require_role(["ADMIN"]))])
def eliminar_producto(
    producto_id: int,
    service: ProductoService = Depends(get_producto_service)
):
    #Soft delete
    return service.eliminar_producto(producto_id)


# Relaciones: Categorías ─────────────────────────────────────────────────

@producto_router.post(
    "/{producto_id}/categorias/{categoria_id}",
    status_code=status.HTTP_200_OK, dependencies=[Depends(require_role(["ADMIN", "STOCK"]))]
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
    dependencies=[Depends(require_role(["ADMIN", "STOCK"]))],
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
    dependencies=[Depends(require_role(["ADMIN", "STOCK"]))],
)
def agregar_ingrediente(
    producto_id: int,
    ingrediente_id: int,
    es_removible: Annotated[bool, Query(description="¿Puede el cliente quitar este ingrediente?")] = False,
    service: ProductoService = Depends(get_producto_service)
):
    return service.agregar_ingrediente(producto_id, ingrediente_id, es_removible)


@producto_router.delete(
    "/{producto_id}/ingredientes/{ingrediente_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_role(["ADMIN", "STOCK"]))],
)
def quitar_ingrediente(
    producto_id: int,
    ingrediente_id: int,
    service: ProductoService = Depends(get_producto_service)
):
    return service.quitar_ingrediente(producto_id, ingrediente_id)
