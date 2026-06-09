from typing import Optional, List, TYPE_CHECKING
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship
 
if TYPE_CHECKING:
    from app.modules.producto.producto_model import Producto
    from app.modules.producto_ingrediente.producto_ingrediente_model import ProductoIngrediente
 
 
class UnidadMedida(SQLModel, table=True):
    __tablename__ = "unidad_medida"
 
    # PK
    id: Optional[int] = Field(default=None, primary_key=True)
 
    # Atributos
    nombre: str = Field(max_length=50, unique=True, nullable=False)
    simbolo: str = Field(max_length=10, unique=True, nullable=False)
    tipo: str = Field(max_length=20, nullable=False)
 
    # Audit
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
 
    # Relaciones
    productos: List["Producto"] = Relationship(back_populates="unidad_venta")
    producto_ingredientes: List["ProductoIngrediente"] = Relationship(back_populates="unidad_medida")