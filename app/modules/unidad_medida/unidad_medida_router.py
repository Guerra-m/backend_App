from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Query, status

from app.core.deps import get_current_active_user, require_role
from app.modules.usuario.usuario_schema import UsuarioAuth
from app.modules.unidad_medida.unidad_medida_schema import (
    UnidadMedidaCreate, UnidadMedidaUpdate, UnidadMedidaRead
)
from app.modules.unidad_medida.unidad_medida_service import UnidadMedidaService
from app.modules.unidad_medida.unidad_medida_uow import UnidadMedidaUnitOfWork

unidad_medida_router = APIRouter(
    prefix="/api/v1/unidades-medida",
    tags=["Unidades de Medida"],
)


def get_service() -> UnidadMedidaService:
    return UnidadMedidaService(UnidadMedidaUnitOfWork())


@unidad_medida_router.get("/", response_model=list[UnidadMedidaRead])
def listar(
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    tipo: Annotated[Optional[str], Query(description="Filtrar por tipo: peso, volumen, contable")] = None,
    _user: Annotated[UsuarioAuth, Depends(get_current_active_user)] = None,
    service: UnidadMedidaService = Depends(get_service),
):
    if tipo:
        return service.listar_por_tipo(tipo)
    return service.listar(offset=offset, limit=limit)


@unidad_medida_router.get("/{unidad_id}", response_model=UnidadMedidaRead)
def obtener(
    unidad_id: int,
    _user: Annotated[UsuarioAuth, Depends(get_current_active_user)] = None,
    service: UnidadMedidaService = Depends(get_service),
):
    return service.obtener(unidad_id)


@unidad_medida_router.post(
    "/",
    response_model=UnidadMedidaRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(["ADMIN"]))],
)
def crear(
    data: UnidadMedidaCreate,
    service: UnidadMedidaService = Depends(get_service),
):
    return service.crear(data)


@unidad_medida_router.put(
    "/{unidad_id}",
    response_model=UnidadMedidaRead,
    dependencies=[Depends(require_role(["ADMIN"]))],
)
def actualizar(
    unidad_id: int,
    data: UnidadMedidaUpdate,
    service: UnidadMedidaService = Depends(get_service),
):
    return service.actualizar(unidad_id, data)


@unidad_medida_router.delete(
    "/{unidad_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_role(["ADMIN"]))],
)
def eliminar(
    unidad_id: int,
    service: UnidadMedidaService = Depends(get_service),
):
    return service.eliminar(unidad_id)