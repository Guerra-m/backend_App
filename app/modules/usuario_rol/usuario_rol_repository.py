from sqlmodel import Session, select
from app.modules.usuario_rol.usuario_rol_model import UsuarioRol


class UsuarioRolRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, usuario_rol: UsuarioRol) -> UsuarioRol:
        self.session.add(usuario_rol)
        self.session.flush()
        return usuario_rol

    def get_roles_by_usuario(self, usuario_id: int) -> list[str]:
        """Retorna la lista de códigos de rol asignados al usuario."""
        statement = select(UsuarioRol.rol_codigo).where(
            UsuarioRol.usuario_id == usuario_id
        )
        return list(self.session.exec(statement).all())

    def get_by_pk(self, usuario_id: int, rol_codigo: str) -> UsuarioRol | None:
        return self.session.get(UsuarioRol, (usuario_id, rol_codigo))

    def delete(self, usuario_id: int, rol_codigo: str) -> None:
        link = self.get_by_pk(usuario_id, rol_codigo)
        if not link:
            raise ValueError(
                f"No existe vínculo entre usuario {usuario_id} y rol {rol_codigo}"
            )
        self.session.delete(link)
        self.session.flush()
