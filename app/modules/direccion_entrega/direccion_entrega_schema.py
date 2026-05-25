from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class DireccionEntregaCreate(BaseModel):
    alias: Optional[str] = Field(default=None, max_length=50)
    linea1: str
    linea2: Optional[str] = None
    ciudad: str = Field(max_length=100)
    provincia: Optional[str] = Field(default=None, max_length=100)
    codigo_postal: Optional[str] = Field(default=None, max_length=10)
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    es_principal: bool = False


class DireccionEntregaUpdate(BaseModel):
    alias: Optional[str] = None
    linea1: Optional[str] = None
    linea2: Optional[str] = None
    ciudad: Optional[str] = None
    provincia: Optional[str] = None
    codigo_postal: Optional[str] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    es_principal: Optional[bool] = None


class DireccionEntregaRead(BaseModel):
    id: int
    usuario_id: int
    alias: Optional[str]
    linea1: str
    linea2: Optional[str]
    ciudad: str
    provincia: Optional[str]
    codigo_postal: Optional[str]
    latitud: Optional[float]
    longitud: Optional[float]
    es_principal: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
