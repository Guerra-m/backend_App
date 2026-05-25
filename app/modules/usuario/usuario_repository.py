from datetime import datetime, timezone
from sqlmodel import Session, select
from app.modules.usuario.usuario_model import Usuario
from app.modules.usuario.usuario_schema import UsuarioCreate, UsuarioUpdate
from app.core.base_repository import BaseRepository
from app.modules.usuario_rol.usuario_rol_model import UsuarioRol


class UsuarioRepository(BaseRepository[Usuario]):
    def __init__(self, session: Session):
        super().__init__(Usuario, session)

    def create(self, usuario: Usuario) -> Usuario:
        self.session.add(usuario)
        self.session.flush()
        self.session.refresh(usuario)
        return usuario

    def get_by_id(self, usuario_id: int) -> Usuario | None:
        usuario = self.session.get(Usuario, usuario_id)
        if usuario and usuario.deleted_at is not None:
            return None
        return usuario

    def get_by_email(self, email: str) -> Usuario | None:
        statement = select(Usuario).where(
            Usuario.email == email,
            Usuario.deleted_at == None,
        )
        return self.session.exec(statement).first()

    def get_all(self, offset: int = 0, limit: int = 20, rol: str | None = None) -> list[Usuario]:
        statement = select(Usuario).where(Usuario.deleted_at == None)

        if rol:
            statement = statement.join(UsuarioRol, UsuarioRol.usuario_id == Usuario.id).where(
                UsuarioRol.rol_codigo == rol
            )

        statement = statement.offset(offset).limit(limit)
        return list(self.session.exec(statement).all())

    def update(self, usuario: Usuario) -> Usuario:
        usuario.updated_at = datetime.now(timezone.utc)
        self.session.add(usuario)
        self.session.flush()
        self.session.refresh(usuario)
        return usuario

    def soft_delete(self, usuario_id: int) -> Usuario:
        usuario = self.session.get(Usuario, usuario_id)
        if not usuario or usuario.deleted_at is not None:
            raise ValueError(f"Usuario con id {usuario_id} no encontrado")
        usuario.deleted_at = datetime.now(timezone.utc)
        self.session.add(usuario)
        self.session.flush()
        return usuario
