from sqlmodel import Session, select
from app.core.base_repository import BaseRepository
from app.modules.unidad_medida.unidad_medida_model import UnidadMedida
from app.modules.unidad_medida.unidad_medida_schema import UnidadMedidaCreate, UnidadMedidaUpdate
from datetime import datetime, timezone
 
 
class UnidadMedidaRepository(BaseRepository[UnidadMedida]):
 
    def __init__(self, session: Session):
        super().__init__(UnidadMedida, session)
 
    def get_by_id(self, unidad_id: int) -> UnidadMedida:
        unidad = self.session.get(UnidadMedida, unidad_id)
        if not unidad:
            raise ValueError(f"UnidadMedida con id {unidad_id} no encontrada")
        return unidad
 
    def get_all(self, offset: int = 0, limit: int = 20) -> list[UnidadMedida]:
        statement = select(UnidadMedida).offset(offset).limit(limit)
        return list(self.session.exec(statement).all())
 
    def get_by_tipo(self, tipo: str) -> list[UnidadMedida]:
        statement = select(UnidadMedida).where(UnidadMedida.tipo == tipo)
        return list(self.session.exec(statement).all())
 
    def create(self, data: UnidadMedidaCreate) -> UnidadMedida:
        unidad = UnidadMedida(**data.model_dump())
        self.session.add(unidad)
        self.session.flush()
        return unidad
 
    def update(self, unidad_id: int, data: UnidadMedidaUpdate) -> UnidadMedida:
        unidad = self.get_by_id(unidad_id)
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(unidad, key, value)
        self.session.add(unidad)
        self.session.flush()
        return unidad
 
    def delete(self, unidad_id: int) -> None:
        unidad = self.get_by_id(unidad_id)
        self.session.delete(unidad)
        self.session.flush()