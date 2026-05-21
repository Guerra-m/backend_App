from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


class CategoriaCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    imagen_url: Optional[str] = None
    parent_id: Optional[int] = None


class CategoriaUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    imagen_url: Optional[str] = None
    parent_id: Optional[int] = None


class CategoriaRead(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str]
    imagen_url: Optional[str]
    parent_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

#Categoria con subcategorias
class CategoriaReadWithSubs(CategoriaRead):
    
    subcategorias: List[CategoriaRead] = []

    model_config = {"from_attributes": True}
