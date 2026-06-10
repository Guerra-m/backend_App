from pydantic import BaseModel, Field


class ProductoIngredienteCreate(BaseModel):
    producto_id: int
    ingrediente_id: int
    es_removible: bool = False
    cantidad: float = Field(gt=0)
    unidad_medida_id: int


class ProductoIngredienteRead(BaseModel):
    producto_id: int
    ingrediente_id: int
    es_removible: bool
    cantidad: float
    unidad_medida_id: int

    model_config = {"from_attributes": True}
