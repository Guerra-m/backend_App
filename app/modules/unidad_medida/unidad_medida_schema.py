from pydantic import BaseModel
from datetime import datetime
 
 
class UnidadMedidaCreate(BaseModel):
    nombre: str
    simbolo: str
    tipo: str
 
 
class UnidadMedidaUpdate(BaseModel):
    nombre: str | None = None
    simbolo: str | None = None
    tipo: str | None = None
 
 
class UnidadMedidaRead(BaseModel):
    id: int
    nombre: str
    simbolo: str
    tipo: str
    created_at: datetime
 
    model_config = {"from_attributes": True}
 