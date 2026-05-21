from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class IngredienteCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    es_alergeno: bool = False


class IngredienteUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    es_alergeno: Optional[bool] = None


class IngredienteRead(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str]
    es_alergeno: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
