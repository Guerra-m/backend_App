"""DetallePedido — tabla 'detalle_pedido'. PK compuesta. Snapshot inmutable."""

from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.modules.pedido.pedido_model import Pedido
    from app.modules.producto.producto_model import Producto


class DetallePedido(SQLModel, table=True):
    __tablename__ = "detalle_pedido"

    # PK compuesta
    pedido_id: int = Field(foreign_key="pedido.id", primary_key=True, ondelete="CASCADE")
    producto_id: int = Field(foreign_key="producto.id", primary_key=True, ondelete="RESTRICT")

    # Atributos
    cantidad: int = Field(nullable=False, ge=1)

    # Snapshot inmutable desde creación
    nombre_snapshot: str = Field(max_length=200, nullable=False)
    precio_snapshot: float = Field(nullable=False, ge=0)
    subtotal_snap: float = Field(nullable=False)
    personalizacion: Optional[str] = Field(default=None)

    # Audit
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relaciones
    pedido: Optional["Pedido"] = Relationship(back_populates="detalles")

    producto: Optional["Producto"] = Relationship(back_populates="detalles_pedido")