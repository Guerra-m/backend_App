from datetime import datetime, timezone
from sqlmodel import Session, select
from app.modules.direccion_entrega.direccion_entrega_model import DireccionEntrega
from app.modules.direccion_entrega.direccion_entrega_schema import (
    DireccionEntregaCreate,
    DireccionEntregaUpdate,
)


class DireccionEntregaRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, usuario_id: int, data: DireccionEntregaCreate) -> DireccionEntrega:
        direccion = DireccionEntrega(
            usuario_id=usuario_id,
            **data.model_dump(),
        )
        self.session.add(direccion)
        self.session.flush()
        return direccion

    def get_by_id(self, direccion_id: int) -> DireccionEntrega | None:
        direccion = self.session.get(DireccionEntrega, direccion_id)
        if direccion and direccion.deleted_at is not None:
            return None
        return direccion

    def get_by_usuario(self, usuario_id: int) -> list[DireccionEntrega]:
        statement = select(DireccionEntrega).where(
            DireccionEntrega.usuario_id == usuario_id,
            DireccionEntrega.deleted_at == None,
        )
        return list(self.session.exec(statement).all())

    def update(self, direccion: DireccionEntrega, data: DireccionEntregaUpdate) -> DireccionEntrega:
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(direccion, key, value)
        direccion.updated_at = datetime.now(timezone.utc)
        self.session.add(direccion)
        self.session.flush()
        return direccion

    def soft_delete(self, direccion: DireccionEntrega) -> DireccionEntrega:
        direccion.deleted_at = datetime.now(timezone.utc)
        self.session.add(direccion)
        self.session.flush()
        return direccion
