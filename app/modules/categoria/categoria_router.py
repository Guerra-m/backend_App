from typing import Annotated, Optional
from fastapi import APIRouter, Query, status, Depends
from app.modules.categoria.categoria_service import CategoriaService
from app.modules.categoria.categoria_uow import CategoriaUnitOfWork
from app.modules.categoria.categoria_schema import (
    CategoriaCreate, CategoriaUpdate, CategoriaRead, CategoriaReadWithSubs
)

from app.core.deps import get_current_active_user, require_role
from app.modules.usuario.usuario_schema import UsuarioAuth


categoria_router = APIRouter(prefix="/api/v1/categorias", tags=["Categorías"])


def get_categoria_service() -> CategoriaService:
    return CategoriaService(CategoriaUnitOfWork())


# GET ────────────────────────────────────────────────────────────────────
#Trae todas las categorias utilizando el offset y limit para definir que traer
@categoria_router.get("/", response_model=list[CategoriaRead])
def listar_categorias(
    offset: Annotated[int, Query(ge=0, description="Cantidad de registros a omitir")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="Cantidad máxima a devolver")] = 20,
    parent_id: Annotated[Optional[int], Query(description="Filtrar por categoría padre")] = None,
    service: CategoriaService = Depends(get_categoria_service)
):
    return service.listar_categorias(offset=offset, limit=limit, parent_id=parent_id)

#Trae todas las categorias principales/padres
@categoria_router.get("/raices", response_model=list[CategoriaRead])
def listar_raices(
    service: CategoriaService = Depends(get_categoria_service),
):
    return service.listar_raices()
    
#Trae categoria por ID junto a sus subcategorias si es que las tienen
@categoria_router.get("/{categoria_id}", response_model=CategoriaReadWithSubs)
def obtener_categoria(
    categoria_id: int,
    service: CategoriaService = Depends(get_categoria_service)
):
    return service.obtener_categoria(categoria_id)


# POST ───────────────────────────────────────────────────────────────────

@categoria_router.post("/", response_model=CategoriaRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role(["ADMIN"]))])
def crear_categoria(
    data: CategoriaCreate,
    service: CategoriaService = Depends(get_categoria_service)
):
    return service.crear_categoria(data)


# PUT ────────────────────────────────────────────────────────────────────

@categoria_router.put("/{categoria_id}", response_model=CategoriaRead, dependencies=[Depends(require_role(["ADMIN"]))])
def actualizar_categoria(
    categoria_id: int,
    data: CategoriaUpdate,
    service: CategoriaService = Depends(get_categoria_service)
):
    return service.actualizar_categoria(categoria_id, data)


# DELETE ─────────────────────────────────────────────────────────────────

@categoria_router.delete("/{categoria_id}", status_code=status.HTTP_200_OK, dependencies=[Depends(require_role(["ADMIN"]))])
def eliminar_categoria(
    categoria_id: int,
    service: CategoriaService = Depends(get_categoria_service)
):
    """Soft delete: marca deleted_at, no elimina físicamente.
    Si tiene productos activos devuelve 409"""
    return service.eliminar_categoria(categoria_id)
