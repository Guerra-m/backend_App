"""Pedido — tabla principal 'pedido'."""

from typing import Optional, List, TYPE_CHECKING
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.modules.detalle_pedido.detalle_pedido_model import DetallePedido
    from app.modules.forma_pago.forma_pago_model import FormaPago
    from app.modules.estado_pedido.estado_pedido_model import EstadoPedido
    from app.modules.usuario.usuario_model import Usuario
    from app.modules.direccion_entrega.direccion_entrega_model import DireccionEntrega


class Pedido(SQLModel, table=True):
    __tablename__ = "pedido"

    # PK
    id: Optional[int] = Field(default=None, primary_key=True)

    # FK
    usuario_id: int = Field(foreign_key="usuario.id", nullable=False)
    direccion_id: Optional[int] = Field(
        default=None, foreign_key="direccion_entrega.id"
    )  # SET NULL si se elimina la dirección
    estado_codigo: str = Field(
        max_length=20, foreign_key="estado_pedido.codigo", nullable=False
    )
    forma_pago_codigo: str = Field(
        max_length=20, foreign_key="forma_pago.codigo", nullable=False
    )

    # Snapshot monetario inmutable desde creación
    subtotal: float = Field(nullable=False)
    descuento: float = Field(default=0.00)
    costo_envio: float = Field(default=50.00)
    total: float = Field(nullable=False, ge=0)

    # Atributos
    notas: Optional[str] = Field(default=None)

    # Audit
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: Optional[datetime] = Field(default=None)

    # Relaciones
    detalles: List["DetallePedido"] = Relationship(back_populates="pedido")
    forma_pago: Optional["FormaPago"] = Relationship(back_populates="pedidos")
    estado: Optional["EstadoPedido"] = Relationship(back_populates="pedidos")

    usuario: Optional["Usuario"] = Relationship(back_populates="pedidos")
    direccion: Optional["DireccionEntrega"] = Relationship(back_populates="pedidos")
