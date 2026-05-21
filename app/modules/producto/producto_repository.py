from datetime import datetime, timezone
from sqlmodel import Session, select
from app.modules.producto.producto_model import Producto
from app.modules.producto.producto_schema import ProductoCreate, ProductoUpdate


class ProductoRepository:
    def __init__(self, session: Session):
        self.session = session

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

    def soft_delete(self, producto_id: int) -> Producto:
        producto = self.get_by_id(producto_id)
        producto.deleted_at = datetime.now(timezone.utc)
        self.session.add(producto)
        self.session.flush()
        return producto
