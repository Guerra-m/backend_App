from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.deps import get_current_active_user
from app.modules.usuario.usuario_schema import UsuarioAuth
from app.modules.direccion_entrega.direccion_entrega_schema import (
    DireccionEntregaCreate,
    DireccionEntregaUpdate,
    DireccionEntregaRead,
)
from app.modules.direccion_entrega.direccion_entrega_service import DireccionEntregaService
from app.modules.direccion_entrega.direccion_entrega_uow import DireccionEntregaUnitOfWork

direccion_entrega_router = APIRouter(
    prefix="/api/v1/direcciones",
    tags=["Direcciones de Entrega"],
)


def get_service() -> DireccionEntregaService:
    return DireccionEntregaService(DireccionEntregaUnitOfWork())


@direccion_entrega_router.get("/", response_model=list[DireccionEntregaRead])
def listar_mis_direcciones(
    current_user: Annotated[UsuarioAuth, Depends(get_current_active_user)],
    service: DireccionEntregaService = Depends(get_service),
):
    return service.listar_mis_direcciones(current_user.id)


@direccion_entrega_router.post(
    "/",
    response_model=DireccionEntregaRead,
    status_code=status.HTTP_201_CREATED,
)
def crear_direccion(
    data: DireccionEntregaCreate,
    current_user: Annotated[UsuarioAuth, Depends(get_current_active_user)],
    service: DireccionEntregaService = Depends(get_service),
):
    return service.crear(current_user.id, data)


@direccion_entrega_router.put("/{direccion_id}", response_model=DireccionEntregaRead)
def actualizar_direccion(
    direccion_id: int,
    data: DireccionEntregaUpdate,
    current_user: Annotated[UsuarioAuth, Depends(get_current_active_user)],
    service: DireccionEntregaService = Depends(get_service),
):
    return service.actualizar(current_user.id, direccion_id, data)


@direccion_entrega_router.delete("/{direccion_id}", status_code=status.HTTP_200_OK)
def eliminar_direccion(
    direccion_id: int,
    current_user: Annotated[UsuarioAuth, Depends(get_current_active_user)],
    service: DireccionEntregaService = Depends(get_service),
):
    return service.eliminar(current_user.id, direccion_id)

@direccion_entrega_router.patch("/{direccion_id}/principal", response_model=DireccionEntregaRead)
def marcar_como_principal(
    direccion_id: int,
    current_user: Annotated[UsuarioAuth, Depends(get_current_active_user)],
    service: DireccionEntregaService = Depends(get_service),
):
    """Marca una dirección como principal. Desmarca la anterior automáticamente."""
    return service.marcar_principal(current_user.id, direccion_id)