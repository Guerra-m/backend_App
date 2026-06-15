from sqlmodel import Session
from app.core.database import engine
from app.modules.pago.pago_repository import PagoRepository
from app.modules.pedido.pedido_repository import PedidoRepository
from app.modules.historial_estado_pedido.historial_estado_pedido_repository import HistorialEstadoPedidoRepository


class PagoUnitOfWork:

    def __enter__(self):
        self.session = Session(engine, expire_on_commit=False)
        self.pagos = PagoRepository(self.session)
        self.pedidos = PedidoRepository(self.session)
        self.historial = HistorialEstadoPedidoRepository(self.session)
        return self

    def __exit__(self, exc_type, *args):
        if exc_type:
            self.session.rollback()
        else:
            self.session.commit()
        self.session.close()