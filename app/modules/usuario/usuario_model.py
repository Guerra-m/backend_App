"""
Modelo Usuario — tabla 'usuario' en PostgreSQL.
Dominio 1: Identidad & Acceso.

Campos clave para seguridad:
  - password_hash: hash bcrypt (CHAR(60), nunca texto plano)
  - Roles asignados vía tabla intermedia UsuarioRol
  - deleted_at: soft delete
"""

from typing import Optional, List, TYPE_CHECKING
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.modules.usuario_rol.usuario_rol_model import UsuarioRol
    from app.modules.direccion_entrega.direccion_entrega_model import DireccionEntrega
    from app.modules.refresh_token.refresh_token_model import RefreshToken
    from app.modules.pedido.pedido_model import Pedido


class Usuario(SQLModel, table=True):
    __tablename__ = "usuario"

    # PK
    id: Optional[int] = Field(default=None, primary_key=True)

    # Datos personales
    nombre: str = Field(max_length=80, nullable=False)
    apellido: str = Field(max_length=80, nullable=False)
    email: str = Field(max_length=254, unique=True, nullable=False)
    celular: Optional[str] = Field(default=None, max_length=20)
    password_hash: str = Field(max_length=60, nullable=False)

    # Audit
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: Optional[datetime] = Field(default=None)

    # Relaciones
    roles_link: List["UsuarioRol"] = Relationship(
        back_populates="usuario",
        sa_relationship_kwargs={"foreign_keys": "[UsuarioRol.usuario_id]"}
    )
    direcciones: List["DireccionEntrega"] = Relationship(back_populates="usuario")
    refresh_tokens: List["RefreshToken"] = Relationship(back_populates="usuario")

    pedidos: List["Pedido"] = Relationship(back_populates="usuario")