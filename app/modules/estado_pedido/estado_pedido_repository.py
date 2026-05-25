from sqlmodel import Session, select
from app.core.base_repository import BaseRepository
from app.modules.estado_pedido.estado_pedido_model import EstadoPedido


class EstadoPedidoRepository(BaseRepository[EstadoPedido]):

    def __init__(self, session: Session):
        super().__init__(EstadoPedido, session)

    def get_all_ordenados(self) -> list[EstadoPedido]:
        return list(self.session.exec(
            select(EstadoPedido).order_by(EstadoPedido.orden)
        ).all())
