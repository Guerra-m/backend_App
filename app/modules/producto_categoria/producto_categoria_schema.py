from pydantic import BaseModel
from datetime import datetime


class ProductoCategoriaCreate(BaseModel):
    producto_id: int
    categoria_id: int
    es_principal: bool = False


class ProductoCategoriaRead(BaseModel):
    producto_id: int
    categoria_id: int
    es_principal: bool
    created_at: datetime

    model_config = {"from_attributes": True}
