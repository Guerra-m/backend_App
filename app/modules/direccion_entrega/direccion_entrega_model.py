from typing import List, Optional, TYPE_CHECKING
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.modules.usuario.usuario_model import Usuario
    from app.modules.pedido.pedido_model import Pedido


class DireccionEntrega(SQLModel, table=True):
    __tablename__ = "direccion_entrega"

    # PK
    id: Optional[int] = Field(default=None, primary_key=True)

    # FK
    usuario_id: int = Field(foreign_key="usuario.id", nullable=False)

    # Atributos
    alias: Optional[str] = Field(default=None, max_length=50)
    linea1: str = Field(nullable=False)
    linea2: Optional[str] = Field(default=None)
    ciudad: str = Field(max_length=100, nullable=False)
    provincia: Optional[str] = Field(default=None, max_length=100)
    codigo_postal: Optional[str] = Field(default=None, max_length=10)
    latitud: Optional[float] = Field(default=None)
    longitud: Optional[float] = Field(default=None)
    es_principal: bool = Field(default=False, nullable=False)

    # Audit
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: Optional[datetime] = Field(default=None)

    # Relaciones
    usuario: Optional["Usuario"] = Relationship(back_populates="direcciones")

    pedidos: List["Pedido"] = Relationship(back_populates="direccion")