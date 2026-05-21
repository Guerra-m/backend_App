from typing import Optional, List, TYPE_CHECKING
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.modules.producto_ingrediente.producto_ingrediente_model import ProductoIngrediente


class Ingrediente(SQLModel, table=True):
    __tablename__ = "ingrediente"

    # PK
    id: Optional[int] = Field(default=None, primary_key=True)

    # Atributos
    nombre: str = Field(max_length=100, unique=True, nullable=False)
    descripcion: Optional[str] = Field(default=None)
    es_alergeno: bool = Field(default=False, nullable=False)

    # Audit
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relaciones
    productos_link: List["ProductoIngrediente"] = Relationship(back_populates="ingrediente")
