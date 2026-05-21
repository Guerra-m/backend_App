from typing import Annotated
from fastapi import APIRouter, Query, status, Depends
from app.modules.ingrediente.ingrediente_service import IngredienteService
from app.modules.ingrediente.ingrediente_uow import IngredienteUnitOfWork
from app.modules.ingrediente.ingrediente_schema import (
    IngredienteCreate, IngredienteUpdate, IngredienteRead
)

from app.core.deps import get_current_active_user, require_role
from app.modules.usuario.usuario_schema import UsuarioAuth

ingrediente_router = APIRouter(prefix="/ingredientes", tags=["Ingredientes"])


def get_ingrediente_service() -> IngredienteService:
    return IngredienteService(IngredienteUnitOfWork())


# GET ────────────────────────────────────────────────────────────────────

@ingrediente_router.get("/", response_model=list[IngredienteRead])
def listar_ingredientes(
    
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    service: IngredienteService = Depends(get_ingrediente_service)
):
    return service.listar_ingredientes(offset=offset, limit=limit)


@ingrediente_router.get("/alergenos", response_model=list[IngredienteRead])
def listar_alergenos(
    _user: Annotated[UsuarioAuth, Depends(get_current_active_user)],
    service: IngredienteService = Depends(get_ingrediente_service),
):
    return service.listar_alergenos()

@ingrediente_router.get("/{ingrediente_id}", response_model=IngredienteRead)
def obtener_ingrediente(
    ingrediente_id: int,
    _user: Annotated[UsuarioAuth, Depends(get_current_active_user)],
    service: IngredienteService = Depends(get_ingrediente_service)
):
    return service.obtener_ingrediente(ingrediente_id)


# POST ───────────────────────────────────────────────────────────────────

@ingrediente_router.post("/", response_model=IngredienteRead, status_code=status.HTTP_201_CREATED, 
                         dependencies=[Depends(require_role(["ADMIN", "STOCK"]))],)
def crear_ingrediente(
    data: IngredienteCreate,
    service: IngredienteService = Depends(get_ingrediente_service)
):
    return service.crear_ingrediente(data)


# PUT ────────────────────────────────────────────────────────────────────

@ingrediente_router.put("/{ingrediente_id}", response_model=IngredienteRead,
                        dependencies=[Depends(require_role(["ADMIN", "STOCK"]))],)
def actualizar_ingrediente(
    ingrediente_id: int,
    data: IngredienteUpdate,
    service: IngredienteService = Depends(get_ingrediente_service)
):
    return service.actualizar_ingrediente(ingrediente_id, data)


# DELETE ─────────────────────────────────────────────────────────────────

@ingrediente_router.delete("/{ingrediente_id}", status_code=status.HTTP_200_OK,
                           dependencies=[Depends(require_role(["ADMIN"]))],)
def eliminar_ingrediente(
    ingrediente_id: int,
    service: IngredienteService = Depends(get_ingrediente_service)
):
    return service.eliminar_ingrediente(ingrediente_id)
