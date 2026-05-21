from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class UsuarioRolCreate(BaseModel):
    usuario_id: int
    rol_codigo: str
    asignado_por_id: Optional[int] = None
    expires_at: Optional[datetime] = None


class UsuarioRolRead(BaseModel):
    usuario_id: int
    rol_codigo: str
    asignado_por_id: Optional[int]
    expires_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}
