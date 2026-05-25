from datetime import datetime, timezone
from sqlmodel import Session, select
from app.modules.producto.producto_model import Producto
from app.modules.producto.producto_schema import ProductoCreate, ProductoUpdate
from app.core.base_repository import BaseRepository


class ProductoRepository(BaseRepository[Producto]):
    def __init__(self, session: Session):
        super().__init__(Producto, session)

    def create(self, data: ProductoCreate) -> Producto:
        producto = Producto(**data.model_dump())
        self.session.add(producto)
        self.session.flush()
        return producto

    def get_by_id(self, producto_id: int) -> Producto:
        producto = self.session.get(Producto, producto_id)
        if not producto or producto.deleted_at is not None:
            raise ValueError(f"Producto con id {producto_id} no encontrado")
        return producto

    def get_all(self, offset: int = 0, limit: int = 20) -> list[Producto]:
        statement = (
            select(Producto)
            .where(Producto.deleted_at == None)
            .offset(offset)
            .limit(limit)
        )
        return self.session.exec(statement).all()
    
    def get_all_filtrado(
        self,
        offset: int = 0,
        limit: int = 20,
        categoria_id: int | None = None,
        disponible: bool | None = None,
        texto: str | None = None,
    ) -> list[Producto]:
        """Listado con filtros: categoría, disponibilidad, búsqueda por texto."""
        from app.modules.producto_categoria.producto_categoria_model import ProductoCategoria

        statement = select(Producto).where(Producto.deleted_at == None)

        if disponible is not None:
            statement = statement.where(Producto.disponible == disponible)

        if texto:
            statement = statement.where(Producto.nombre.ilike(f"%{texto}%"))

        if categoria_id is not None:
            statement = statement.join(
                ProductoCategoria,
                ProductoCategoria.producto_id == Producto.id
            ).where(ProductoCategoria.categoria_id == categoria_id)

        statement = statement.offset(offset).limit(limit)
        return list(self.session.exec(statement).all())

    def get_disponibles(self, offset: int = 0, limit: int = 20) -> list[Producto]:
        #Devuelve solo productos activos y con stock
        statement = (
            select(Producto)
            .where(
                Producto.deleted_at == None,
                Producto.disponible == True,
                Producto.stock_cantidad > 0
            )
            .offset(offset)
            .limit(limit)
        )
        return self.session.exec(statement).all()

    def update(self, producto_id: int, data: ProductoUpdate) -> Producto:
        producto = self.get_by_id(producto_id)
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(producto, key, value)
        producto.updated_at = datetime.now(timezone.utc)
        self.session.add(producto)
        self.session.flush()
        return producto
    
    def actualizar_disponibilidad(
        self, producto_id: int, disponible: bool, stock_cantidad: int | None = None
    ) -> Producto:
        """PATCH /disponibilidad — ADMIN y STOCK pueden usar esto."""
        producto = self.get_by_id(producto_id)
        producto.disponible = disponible
        if stock_cantidad is not None:
            producto.stock_cantidad = stock_cantidad
        producto.updated_at = datetime.now(timezone.utc)
        self.session.add(producto)
        self.session.flush()
        return producto

    def soft_delete(self, producto_id: int) -> Producto:
        producto = self.get_by_id(producto_id)
        producto.deleted_at = datetime.now(timezone.utc)
        self.session.add(producto)
        self.session.flush()
        return producto
