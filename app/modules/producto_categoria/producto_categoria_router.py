from typing import Annotated

from fastapi import APIRouter, status, Depends
from app.modules.producto_categoria.producto_categoria_service import ProductoCategoriaService
from app.modules.producto_categoria.producto_categoria_uow import ProductoCategoriaUnitOfWork
from app.modules.producto_categoria.producto_categoria_schema import (
    ProductoCategoriaCreate, ProductoCategoriaRead
)

from app.core.deps import get_current_active_user, require_role
from app.modules.usuario.usuario_schema import UsuarioAuth

producto_categoria_router = APIRouter(
    prefix="/api/v1/producto-categorias",
    tags=["ProductoCategoria"]
)


def get_service() -> ProductoCategoriaService:
    return ProductoCategoriaService(ProductoCategoriaUnitOfWork())


@producto_categoria_router.post("/", response_model=ProductoCategoriaRead, status_code=status.HTTP_201_CREATED,
                                 dependencies=[Depends(require_role(["ADMIN", "STOCK"]))],)
def vincular(
    data: ProductoCategoriaCreate,
    service: ProductoCategoriaService = Depends(get_service)
):
    return service.vincular(data)


@producto_categoria_router.get("/producto/{producto_id}", 
                               response_model=list[ProductoCategoriaRead])
def por_producto(
    producto_id: int,
    _user: Annotated[UsuarioAuth, Depends(get_current_active_user)],
    service: ProductoCategoriaService = Depends(get_service)
):
    return service.listar_por_producto(producto_id)


@producto_categoria_router.get("/categoria/{categoria_id}", response_model=list[ProductoCategoriaRead])
def por_categoria(
    categoria_id: int,
    _user: Annotated[UsuarioAuth, Depends(get_current_active_user)],
    service: ProductoCategoriaService = Depends(get_service)
):
    return service.listar_por_categoria(categoria_id)


@producto_categoria_router.delete(
        "/{producto_id}/{categoria_id}", 
        status_code=status.HTTP_200_OK, 
        dependencies=[Depends(require_role(["ADMIN", "STOCK"]))])
def desvincular(
    producto_id: int,
    categoria_id: int,
    service: ProductoCategoriaService = Depends(get_service)
):
    return service.desvincular(producto_id, categoria_id)
