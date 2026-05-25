import json
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, model_validator


class ItemPedidoCreate(BaseModel):
    producto_id: int
    cantidad: int = Field(ge=1)
    personalizacion: list[int] = []


class DetallePedidoRead(BaseModel):
    pedido_id: int
    producto_id: int
    cantidad: int
    nombre_snapshot: str
    precio_snapshot: float
    subtotal_snap: float
    personalizacion: Optional[list[int]] = []
    created_at: datetime

    model_config = {"from_attributes": True}

    @model_validator(mode="after")
    def deserializar_personalizacion(self) -> "DetallePedidoRead":
        if isinstance(self.personalizacion, str):
            try:
                self.personalizacion = json.loads(self.personalizacion)
            except Exception:
                self.personalizacion = []
        return self