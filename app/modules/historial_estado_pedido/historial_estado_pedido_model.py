from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.modules.estado_pedido.estado_pedido_model import EstadoPedido


class HistorialEstadoPedido(SQLModel, table=True):
    __tablename__ = "historial_estado_pedido"

    # PK
    id: Optional[int] = Field(default=None, primary_key=True)

    # FK de trazabilidad
    pedido_id: int = Field(foreign_key="pedido.id", nullable=False, ondelete="CASCADE")
    estado_desde: Optional[str] = Field(
        default=None, max_length=20, foreign_key="estado_pedido.codigo"
    )  # NULL = creación del pedido
    estado_hacia: str = Field(max_length=20, foreign_key="estado_pedido.codigo", nullable=False)
    usuario_id: Optional[int] = Field(
        default=None, foreign_key="usuario.id"
    )  # NULL = actor es el sistema

    # Atributos
    motivo: Optional[str] = Field(default=None)

    # Audit — append-only
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relaciones
    estado_desde_rel: Optional["EstadoPedido"] = Relationship(
        back_populates="historial_desde",
        sa_relationship_kwargs={"foreign_keys": "[HistorialEstadoPedido.estado_desde]"}
    )
    estado_hacia_rel: Optional["EstadoPedido"] = Relationship(
        back_populates="historial_hacia",
        sa_relationship_kwargs={"foreign_keys": "[HistorialEstadoPedido.estado_hacia]"}
    )
