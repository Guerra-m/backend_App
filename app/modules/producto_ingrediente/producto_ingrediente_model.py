from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.modules.producto.producto_model import Producto
    from app.modules.ingrediente.ingrediente_model import Ingrediente
    from app.modules.unidad_medida.unidad_medida_model import UnidadMedida


class ProductoIngrediente(SQLModel, table=True):
    __tablename__ = "producto_ingrediente"

    # PK compuesta
    producto_id: int = Field(foreign_key="producto.id", primary_key=True)
    ingrediente_id: int = Field(foreign_key="ingrediente.id", primary_key=True)

    # Atributos
    es_removible: bool = Field(default=False, nullable=False)
    cantidad: float = Field(nullable=False, gt=0)
    unidad_medida_id: int = Field(foreign_key="unidad_medida.id", nullable=False)

    # Relaciones
    producto: Optional["Producto"] = Relationship(back_populates="ingredientes_link")
    ingrediente: Optional["Ingrediente"] = Relationship(back_populates="productos_link")
    unidad_medida: Optional["UnidadMedida"] = Relationship(back_populates="producto_ingredientes")
