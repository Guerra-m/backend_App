from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship
 
if TYPE_CHECKING:
    from app.modules.pedido.pedido_model import Pedido
 
 
class Pago(SQLModel, table=True):
    __tablename__ = "pago"
 
    # PK
    id: Optional[int] = Field(default=None, primary_key=True)
 
    # FK
    pedido_id: int = Field(foreign_key="pedido.id", nullable=False, ondelete="RESTRICT")
 
    # MercadoPago
    mp_payment_id: Optional[int] = Field(default=None, unique=True)
    mp_status: str = Field(max_length=30, nullable=False)
    mp_status_detail: Optional[str] = Field(default=None, max_length=100)
    external_reference: str = Field(max_length=100, unique=True, nullable=False)
    idempotency_key: str = Field(max_length=100, unique=True, nullable=False)
    transaction_amount: float = Field(nullable=False)
    payment_method_id: Optional[str] = Field(default=None, max_length=50)
 
    # Audit
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
 
    # Relaciones
    pedido: Optional["Pedido"] = Relationship(back_populates="pago")