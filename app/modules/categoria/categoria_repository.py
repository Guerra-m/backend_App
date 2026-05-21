from datetime import datetime, timezone
from sqlmodel import Session, select
from app.modules.categoria.categoria_model import Categoria
from app.modules.categoria.categoria_schema import CategoriaCreate, CategoriaUpdate


class CategoriaRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, data: CategoriaCreate) -> Categoria:
        categoria = Categoria(**data.model_dump())
        self.session.add(categoria)
        self.session.flush()
        return categoria

    def get_by_id(self, categoria_id: int) -> Categoria:
        categoria = self.session.get(Categoria, categoria_id)
        if not categoria or categoria.deleted_at is not None:
            raise ValueError(f"Categoría con id {categoria_id} no encontrada")
        return categoria

    def get_all(self, offset: int = 0, limit: int = 20) -> list[Categoria]:
        statement = (
            select(Categoria)
            .where(Categoria.deleted_at == None)
            .offset(offset)
            .limit(limit)
        )
        return self.session.exec(statement).all()

    def get_raices(self) -> list[Categoria]:
        """Devuelve solo las categorías sin padre (nivel raíz)."""
        statement = select(Categoria).where(
            Categoria.parent_id == None,
            Categoria.deleted_at == None
        )
        return self.session.exec(statement).all()

    def update(self, categoria_id: int, data: CategoriaUpdate) -> Categoria:
        categoria = self.get_by_id(categoria_id)
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(categoria, key, value)
        categoria.updated_at = datetime.now(timezone.utc)
        self.session.add(categoria)
        self.session.flush()
        return categoria

    def soft_delete(self, categoria_id: int) -> Categoria:
        categoria = self.get_by_id(categoria_id)
        categoria.deleted_at = datetime.now(timezone.utc)
        self.session.add(categoria)
        self.session.flush()
        return categoria
