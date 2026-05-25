from sqlmodel import Session, select
from app.core.base_repository import BaseRepository
from app.modules.rol.rol_model import Rol


class RolRepository(BaseRepository[Rol]):
    def __init__(self, session: Session):
        super().__init__(Rol, session)

    def get_by_codigo(self, codigo: str) -> Rol | None:
        return self.session.get(Rol, codigo)

    def get_all(self) -> list[Rol]:
        return list(self.session.exec(select(Rol)).all())
