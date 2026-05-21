from pydantic import BaseModel


class ProductoIngredienteCreate(BaseModel):
    producto_id: int
    ingrediente_id: int
    es_removible: bool = False


class ProductoIngredienteRead(BaseModel):
    producto_id: int
    ingrediente_id: int
    es_removible: bool

    model_config = {"from_attributes": True}
