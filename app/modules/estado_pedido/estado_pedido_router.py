from typing import Annotated
from fastapi import APIRouter, Depends
from sqlmodel import Session
from app.core.database import engine
from app.core.deps import get_current_active_user
from app.modules.usuario.usuario_schema import UsuarioAuth
from app.modules.estado_pedido.estado_pedido_schema import EstadoPedidoRead
from app.modules.estado_pedido.estado_pedido_repository import EstadoPedidoRepository

estado_pedido_router = APIRouter(
    prefix="/api/v1/estados-pedido", 
    tags=["Estados de Pedido"])


@estado_pedido_router.get("/", response_model=list[EstadoPedidoRead])
def listar_estados(
    _user: Annotated[UsuarioAuth, Depends(get_current_active_user)],
):
    with Session(engine) as session:
        repo = EstadoPedidoRepository(session)
        return [EstadoPedidoRead.model_validate(e) for e in repo.get_all_ordenados()]
