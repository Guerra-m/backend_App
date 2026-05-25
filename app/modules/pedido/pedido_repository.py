"""Repositorio de Pedido — extiende BaseRepository con queries propias."""

from datetime import datetime, timezone
from sqlmodel import Session, select
from app.core.base_repository import BaseRepository
from app.modules.pedido.pedido_model import Pedido


class PedidoRepository(BaseRepository[Pedido]):

    def __init__(self, session: Session):
        super().__init__(Pedido, session)

    def get_by_id_activo(self, pedido_id: int) -> Pedido | None:
        pedido = self.session.get(Pedido, pedido_id)
        if pedido and pedido.deleted_at is not None:
            return None
        return pedido

    def get_all_activos(self, offset: int = 0, limit: int = 20) -> list[Pedido]:
        """ADMIN/PEDIDOS: ve todos los pedidos."""
        statement = (
            select(Pedido)
            .where(Pedido.deleted_at == None)
            .order_by(Pedido.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.exec(statement).all())

    def get_by_usuario(self, usuario_id: int, offset: int = 0, limit: int = 20) -> list[Pedido]:
        """CLIENT: solo ve sus propios pedidos."""
        statement = (
            select(Pedido)
            .where(Pedido.usuario_id == usuario_id, Pedido.deleted_at == None)
            .order_by(Pedido.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.exec(statement).all())

    def actualizar_estado(self, pedido: Pedido, nuevo_estado: str) -> Pedido:
        pedido.estado_codigo = nuevo_estado
        pedido.updated_at = datetime.now(timezone.utc)
        self.session.add(pedido)
        self.session.flush()
        self.session.refresh(pedido)
        return pedido

    def soft_delete(self, pedido: Pedido) -> Pedido:
        pedido.deleted_at = datetime.now(timezone.utc)
        self.session.add(pedido)
        self.session.flush()
        return pedido
