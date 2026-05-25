from pydantic import BaseModel


class FormaPagoRead(BaseModel):
    codigo: str
    descripcion: str
    habilitado: bool

    model_config = {"from_attributes": True}
