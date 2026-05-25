from datetime import datetime, timezone
from sqlmodel import Session, select
from app.modules.categoria.categoria_model import Categoria
from app.modules.categoria.categoria_schema import CategoriaCreate, CategoriaUpdate
from app.core.base_repository import BaseRepository

class CategoriaRepository(BaseRepository[Categoria]):
    def __init__(self, session: Session):
        super().__init__(Categoria, session)

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

    def get_all(self, offset: int = 0, limit: int = 20, parent_id: int | None = None) -> list[Categoria]:
        statement = select(Categoria).where(Categoria.deleted_at == None)

        if parent_id is not None:
            statement = statement.where(Categoria.parent_id == parent_id)

        statement = statement.offset(offset).limit(limit)
        return list(self.session.exec(statement).all())

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

    def tiene_productos_activos(self, categoria_id: int) -> bool:
        """Verifica si la categoría tiene productos activos vinculados (para validar soft delete)."""
        from app.modules.producto_categoria.producto_categoria_model import ProductoCategoria
        from app.modules.producto.producto_model import Producto
        statement = (
            select(ProductoCategoria)
            .join(Producto, Producto.id == ProductoCategoria.producto_id)
            .where(
                ProductoCategoria.categoria_id == categoria_id,
                Producto.deleted_at == None,
            )
        )
        return self.session.exec(statement).first() is not None