from sqlmodel import Session, select
from app.core.base_repository import BaseRepository
from app.modules.detalle_pedido.detalle_pedido_model import DetallePedido


class DetallePedidoRepository(BaseRepository[DetallePedido]):

    def __init__(self, session: Session):
        super().__init__(DetallePedido, session)

    def get_by_pedido(self, pedido_id: int) -> list[DetallePedido]:
        statement = select(DetallePedido).where(DetallePedido.pedido_id == pedido_id)
        return list(self.session.exec(statement).all())

    def get_by_pk(self, pedido_id: int, producto_id: int) -> DetallePedido | None:
        return self.session.get(DetallePedido, (pedido_id, producto_id))
