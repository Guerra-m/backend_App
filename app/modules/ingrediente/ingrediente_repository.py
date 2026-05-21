from datetime import datetime, timezone
from sqlmodel import Session, select
from app.modules.ingrediente.ingrediente_model import Ingrediente
from app.modules.ingrediente.ingrediente_schema import IngredienteCreate, IngredienteUpdate


class IngredienteRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, data: IngredienteCreate) -> Ingrediente:
        ingrediente = Ingrediente(**data.model_dump())
        self.session.add(ingrediente)
        self.session.flush()
        return ingrediente

    def get_by_id(self, ingrediente_id: int) -> Ingrediente:
        ingrediente = self.session.get(Ingrediente, ingrediente_id)
        if not ingrediente:
            raise ValueError(f"Ingrediente con id {ingrediente_id} no encontrado")
        return ingrediente

    def get_all(self, offset: int = 0, limit: int = 20) -> list[Ingrediente]:
        statement = select(Ingrediente).offset(offset).limit(limit)
        return self.session.exec(statement).all()

    def get_alergenos(self) -> list[Ingrediente]:
        #Devuelve solo los ingredientes que son alérgenos
        statement = select(Ingrediente).where(Ingrediente.es_alergeno == True)
        return self.session.exec(statement).all()

    def update(self, ingrediente_id: int, data: IngredienteUpdate) -> Ingrediente:
        ingrediente = self.get_by_id(ingrediente_id)
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(ingrediente, key, value)
        ingrediente.updated_at = datetime.now(timezone.utc)
        self.session.add(ingrediente)
        self.session.flush()
        return ingrediente

    def delete(self, ingrediente_id: int) -> None:
        ingrediente = self.get_by_id(ingrediente_id)
        self.session.delete(ingrediente)
        self.session.flush()
