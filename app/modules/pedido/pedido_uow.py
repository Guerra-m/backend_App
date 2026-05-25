"""
PedidoUnitOfWork — transacción atómica para crear y gestionar pedidos.
Agrupa todos los repositorios necesarios para el dominio de ventas.
"""

from sqlmodel import Session
from app.core.database import engine
from app.modules.pedido.pedido_repository import PedidoRepository
from app.modules.detalle_pedido.detalle_pedido_repository import DetallePedidoRepository
from app.modules.historial_estado_pedido.historial_estado_pedido_repository import HistorialEstadoPedidoRepository
from app.modules.producto.producto_repository import ProductoRepository
from app.modules.forma_pago.forma_pago_repository import FormaPagoRepository
from app.modules.estado_pedido.estado_pedido_repository import EstadoPedidoRepository
from app.modules.direccion_entrega.direccion_entrega_repository import DireccionEntregaRepository


class PedidoUnitOfWork:

    def __enter__(self):
        self.session = Session(engine, expire_on_commit=False)
        self.pedidos = PedidoRepository(self.session)
        self.detalles = DetallePedidoRepository(self.session)
        self.historial = HistorialEstadoPedidoRepository(self.session)
        self.productos = ProductoRepository(self.session)
        self.formas_pago = FormaPagoRepository(self.session)
        self.estados = EstadoPedidoRepository(self.session)
        self.direcciones = DireccionEntregaRepository(self.session)
        return self

    def __exit__(self, exc_type, *args):
        if exc_type:
            self.session.rollback()
        else:
            self.session.commit()
        self.session.close()
