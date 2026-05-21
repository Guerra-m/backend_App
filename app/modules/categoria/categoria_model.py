from typing import Optional, List, TYPE_CHECKING
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.modules.producto_categoria.producto_categoria_model import ProductoCategoria


class Categoria(SQLModel, table=True):
    __tablename__ = "categoria"

    # PK
    id: Optional[int] = Field(default=None, primary_key=True)

    # FK auto-referencia (categoría padre)
    parent_id: Optional[int] = Field(default=None, foreign_key="categoria.id")

    # Atributos
    nombre: str = Field(max_length=100, unique=True, nullable=False)
    descripcion: Optional[str] = Field(default=None)
    imagen_url: Optional[str] = Field(default=None)

    # Audit
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: Optional[datetime] = Field(default=None)

    # Relaciones
    # Hijos de esta categoría (subcategorías)
    subcategorias: List["Categoria"] = Relationship(
        back_populates="parent",
        sa_relationship_kwargs={"foreign_keys": "[Categoria.parent_id]"}
    )
    # Padre de esta categoría
    parent: Optional["Categoria"] = Relationship(
        back_populates="subcategorias",
        sa_relationship_kwargs={
            "foreign_keys": "[Categoria.parent_id]", #Usa esta FK para esta relacion
            "remote_side": "[Categoria.id]" #el lado "padre" es el id
        }
    )

    # Productos vinculados a través de la tabla intermedia
    productos_link: List["ProductoCategoria"] = Relationship(back_populates="categoria")
