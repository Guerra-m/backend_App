from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.modules.usuario.usuario_model import Usuario


class RefreshToken(SQLModel, table=True):
    __tablename__ = "refresh_token"

    # PK
    id: Optional[int] = Field(default=None, primary_key=True)

    # FK
    usuario_id: int = Field(foreign_key="usuario.id", nullable=False)

    # Atributos
    token_hash: str = Field(max_length=64, unique=True, nullable=False)
    expires_at: datetime = Field(nullable=False)
    revoked_at: Optional[datetime] = Field(default=None)

    # Audit
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relaciones
    usuario: Optional["Usuario"] = Relationship(back_populates="refresh_tokens")
