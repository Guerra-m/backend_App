from typing import Optional
from datetime import datetime
from pydantic import BaseModel
 
 
class PagoCreate(BaseModel):
    pedido_id: int
    external_reference: str
    idempotency_key: str
    transaction_amount: float
    mp_status: str = "pending"
    mp_payment_id: Optional[int] = None
    mp_status_detail: Optional[str] = None
    payment_method_id: Optional[str] = None
 
 
class PagoUpdate(BaseModel):
    """Usado al recibir webhook de MercadoPago."""
    mp_payment_id: Optional[int] = None
    mp_status: Optional[str] = None
    mp_status_detail: Optional[str] = None
    transaction_amount: Optional[float] = None
    payment_method_id: Optional[str] = None
 
 
class PagoRead(BaseModel):
    id: int
    pedido_id: int
    mp_payment_id: Optional[int]
    mp_status: str
    mp_status_detail: Optional[str]
    external_reference: str
    idempotency_key: str
    transaction_amount: float
    payment_method_id: Optional[str]
    created_at: datetime
    updated_at: datetime
 
    model_config = {"from_attributes": True}