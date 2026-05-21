"""
Modelo Rol — tabla catálogo 'rol' en PostgreSQL.
PK semántica (codigo), no surrogate. Se pobla vía seed.

Roles del sistema:
  ADMIN   — acceso total sin restricciones
  STOCK   — actualiza stock y disponible
  PEDIDOS — avanza estados CONFIRMADO→ENTREGADO
  CLIENT  — opera solo sus propios datos
"""

from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.modules.usuario_rol.usuario_rol_model import UsuarioRol


class Rol(SQLModel, table=True):
    __tablename__ = "rol"

    # PK semántica (no surrogate)
    codigo: str = Field(max_length=20, primary_key=True)

    # Atributos
    nombre: str = Field(max_length=50, unique=True, nullable=False)
    descripcion: Optional[str] = Field(default=None)

    # Relaciones
    usuarios_link: List["UsuarioRol"] = Relationship(back_populates="rol")
