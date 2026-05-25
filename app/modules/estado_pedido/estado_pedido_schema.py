from pydantic import BaseModel


class EstadoPedidoRead(BaseModel):
    codigo: str
    descripcion: str
    orden: int
    es_terminal: bool

    model_config = {"from_attributes": True}
