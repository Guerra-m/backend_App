from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

from app.modules.detalle_pedido.detalle_pedido_schema import ItemPedidoCreate, DetallePedidoRead
from app.modules.historial_estado_pedido.historial_estado_pedido_schema import HistorialEstadoPedidoRead


class PedidoCreate(BaseModel):
    direccion_id: Optional[int] = None
    forma_pago_codigo: str
    descuento: float = 0.00
    costo_envio: float = 50.00
    notas: Optional[str] = None
    items: list[ItemPedidoCreate] = Field(min_length=1)


class PedidoRead(BaseModel):
    id: int
    usuario_id: int
    direccion_id: Optional[int]
    estado_codigo: str
    forma_pago_codigo: str
    subtotal: float
    descuento: float
    costo_envio: float
    total: float
    notas: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PedidoReadDetalle(PedidoRead):
    """Pedido con detalles e historial completo."""
    detalles: list[DetallePedidoRead] = []
    historial: list[HistorialEstadoPedidoRead] = []

    model_config = {"from_attributes": True}


class AvanzarEstadoRequest(BaseModel):
    estado_hacia: str
    motivo: Optional[str] = None
