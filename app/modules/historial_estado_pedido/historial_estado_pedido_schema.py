from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class HistorialEstadoPedidoRead(BaseModel):
    id: int
    pedido_id: int
    estado_desde: Optional[str]
    estado_hacia: str
    usuario_id: Optional[int]
    motivo: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
