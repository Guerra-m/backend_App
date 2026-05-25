from sqlmodel import Session, select
from app.core.base_repository import BaseRepository
from app.modules.historial_estado_pedido.historial_estado_pedido_model import HistorialEstadoPedido


class HistorialEstadoPedidoRepository(BaseRepository[HistorialEstadoPedido]):

    def __init__(self, session: Session):
        super().__init__(HistorialEstadoPedido, session)

    def get_by_pedido(self, pedido_id: int) -> list[HistorialEstadoPedido]:
        """Devuelve el historial ordenado por fecha ASC (estado actual = último registro)."""
        statement = (
            select(HistorialEstadoPedido)
            .where(HistorialEstadoPedido.pedido_id == pedido_id)
            .order_by(HistorialEstadoPedido.created_at.asc())
        )
        return list(self.session.exec(statement).all())
