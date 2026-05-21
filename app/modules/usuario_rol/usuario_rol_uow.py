from sqlmodel import Session
from app.core.database import engine
from app.modules.usuario_rol.usuario_rol_repository import UsuarioRolRepository
from app.modules.usuario.usuario_repository import UsuarioRepository
from app.modules.rol.rol_repository import RolRepository


class UsuarioRolUnitOfWork:

    def __enter__(self):
        self.session = Session(engine, expire_on_commit=False)
        self.usuario_roles = UsuarioRolRepository(self.session)
        self.usuarios = UsuarioRepository(self.session)
        self.roles = RolRepository(self.session)
        return self

    def __exit__(self, exc_type, *args):
        if exc_type:
            self.session.rollback()
        else:
            self.session.commit()
        self.session.close()
