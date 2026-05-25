"""EstadoPedido — tabla catálogo 'estado_pedido'. PK semántica, seed obligatorio."""

from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.modules.pedido.pedido_model import Pedido
    from app.modules.historial_estado_pedido.historial_estado_pedido_model import HistorialEstadoPedido


class EstadoPedido(SQLModel, table=True):
    __tablename__ = "estado_pedido"

    codigo: str = Field(max_length=20, primary_key=True)
    descripcion: str = Field(max_length=80, nullable=False)
    orden: int = Field(nullable=False)
    es_terminal: bool = Field(nullable=False)

    pedidos: List["Pedido"] = Relationship(back_populates="estado")
    historial_desde: List["HistorialEstadoPedido"] = Relationship(
        back_populates="estado_desde_rel",
        sa_relationship_kwargs={"foreign_keys": "[HistorialEstadoPedido.estado_desde]"}
    )
    historial_hacia: List["HistorialEstadoPedido"] = Relationship(
        back_populates="estado_hacia_rel",
        sa_relationship_kwargs={"foreign_keys": "[HistorialEstadoPedido.estado_hacia]"}
    )
