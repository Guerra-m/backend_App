from typing import Annotated
from fastapi import APIRouter, Depends, Query, status

from app.core.deps import get_current_active_user, require_role
from app.modules.usuario.usuario_schema import UsuarioAuth
from app.modules.pedido.pedido_schema import (
    PedidoCreate, PedidoRead, PedidoReadDetalle, AvanzarEstadoRequest
)
from app.modules.pedido.pedido_service import PedidoService
from app.modules.pedido.pedido_uow import PedidoUnitOfWork
from app.modules.historial_estado_pedido.historial_estado_pedido_schema import HistorialEstadoPedidoRead

pedido_router = APIRouter(prefix="/api/v1/pedidos", tags=["Pedidos"])


def get_pedido_service() -> PedidoService:
    return PedidoService(PedidoUnitOfWork())


@pedido_router.post("/", response_model=PedidoRead, status_code=status.HTTP_201_CREATED)
def crear_pedido(
    data: PedidoCreate,
    current_user: Annotated[UsuarioAuth, Depends(get_current_active_user)],
    service: PedidoService = Depends(get_pedido_service),
):
    return service.crear_pedido(data, current_user)


@pedido_router.get("/", response_model=list[PedidoRead])
def listar_pedidos(
    current_user: Annotated[UsuarioAuth, Depends(get_current_active_user)],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    service: PedidoService = Depends(get_pedido_service),
):
    return service.listar_pedidos(current_user, offset=offset, limit=limit)


@pedido_router.get("/{pedido_id}", response_model=PedidoReadDetalle)
def obtener_pedido(
    pedido_id: int,
    current_user: Annotated[UsuarioAuth, Depends(get_current_active_user)],
    service: PedidoService = Depends(get_pedido_service),
):
    return service.obtener_pedido(pedido_id, current_user)


@pedido_router.post("/{pedido_id}/avanzar", response_model=PedidoRead)
def avanzar_estado(
    pedido_id: int,
    body: AvanzarEstadoRequest,
    current_user: Annotated[UsuarioAuth, Depends(get_current_active_user)],
    service: PedidoService = Depends(get_pedido_service),
):
    """
    Avanza el estado del pedido según la FSM.
    CLIENT: solo puede cancelar desde PENDIENTE o CONFIRMADO.
    ADMIN/PEDIDOS: pueden avanzar cualquier transición válida.
    """
    return service.avanzar_estado(pedido_id, body.estado_hacia, current_user, body.motivo)


@pedido_router.get("/{pedido_id}/historial", response_model=list[HistorialEstadoPedidoRead])
def obtener_historial(
    pedido_id: int,
    current_user: Annotated[UsuarioAuth, Depends(get_current_active_user)],
    service: PedidoService = Depends(get_pedido_service),
):
    return service.obtener_historial(pedido_id, current_user)
