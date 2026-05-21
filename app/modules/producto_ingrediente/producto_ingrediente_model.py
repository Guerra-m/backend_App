from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.modules.producto.producto_model import Producto
    from app.modules.ingrediente.ingrediente_model import Ingrediente


class ProductoIngrediente(SQLModel, table=True):
    __tablename__ = "producto_ingrediente"

    # PK compuesta
    producto_id: int = Field(foreign_key="producto.id", primary_key=True)
    ingrediente_id: int = Field(foreign_key="ingrediente.id", primary_key=True)

    # Atributos
    es_removible: bool = Field(default=False, nullable=False)

    # Relaciones
    producto: Optional["Producto"] = Relationship(back_populates="ingredientes_link")
    ingrediente: Optional["Ingrediente"] = Relationship(back_populates="productos_link")
