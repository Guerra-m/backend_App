from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.modules.producto.producto_model import Producto
    from app.modules.categoria.categoria_model import Categoria


class ProductoCategoria(SQLModel, table=True):
    __tablename__ = "producto_categoria"

    # PK compuesta
    producto_id: int = Field(foreign_key="producto.id", primary_key=True)
    categoria_id: int = Field(foreign_key="categoria.id", primary_key=True)

    # Atributos
    es_principal: bool = Field(default=False, nullable=False)

    # Audit
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relaciones
    producto: Optional["Producto"] = Relationship(back_populates="categorias_link")
    categoria: Optional["Categoria"] = Relationship(back_populates="productos_link")
