from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.modules.usuario.usuario_model import Usuario
    from app.modules.rol.rol_model import Rol


class UsuarioRol(SQLModel, table=True):
    __tablename__ = "usuario_rol"

    # PK compuesta
    usuario_id: int = Field(foreign_key="usuario.id", primary_key=True)
    rol_codigo: str = Field(max_length=20, foreign_key="rol.codigo", primary_key=True)

    # Atributos
    asignado_por_id: Optional[int] = Field(default=None, foreign_key="usuario.id")
    expires_at: Optional[datetime] = Field(default=None)

    # Audit
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relaciones
    usuario: Optional["Usuario"] = Relationship(
        back_populates="roles_link",
        sa_relationship_kwargs={"foreign_keys": "[UsuarioRol.usuario_id]"}
    )
    rol: Optional["Rol"] = Relationship(back_populates="usuarios_link")
