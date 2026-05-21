from typing import Optional, List, TYPE_CHECKING
from datetime import datetime, timezone
from decimal import Decimal
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.modules.producto_categoria.producto_categoria_model import ProductoCategoria
    from app.modules.producto_ingrediente.producto_ingrediente_model import ProductoIngrediente


class Producto(SQLModel, table=True):
    __tablename__ = "producto"

    # PK
    id: Optional[int] = Field(default=None, primary_key=True)

    # Atributos
    nombre: str = Field(max_length=150, nullable=False)
    descripcion: Optional[str] = Field(default=None)
    precio_base: Decimal = Field(decimal_places=2, max_digits=10, nullable=False, ge=0)
    imagenes_url: Optional[str] = Field(default=None)  # JSON string con lista de URLs
    stock_cantidad: int = Field(default=0, nullable=False, ge=0)
    disponible: bool = Field(default=True, nullable=False)

    # Audit
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: Optional[datetime] = Field(default=None)

    # Relaciones
    categorias_link: List["ProductoCategoria"] = Relationship(back_populates="producto")
    ingredientes_link: List["ProductoIngrediente"] = Relationship(back_populates="producto")
