from sqlmodel import Session, select
from app.modules.producto_categoria.producto_categoria_model import ProductoCategoria
from app.modules.producto_categoria.producto_categoria_schema import ProductoCategoriaCreate


class ProductoCategoriaRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, data: ProductoCategoriaCreate) -> ProductoCategoria:
        # Verifica que no exista ya la combinación
        existing = self.session.get(
            ProductoCategoria, (data.producto_id, data.categoria_id)
        )
        if existing:
            raise ValueError(
                f"El producto {data.producto_id} ya está vinculado a la categoría {data.categoria_id}"
            )
        link = ProductoCategoria(**data.model_dump())
        self.session.add(link)
        self.session.flush()
        return link

    def get_by_producto(self, producto_id: int) -> list[ProductoCategoria]:
        statement = select(ProductoCategoria).where(
            ProductoCategoria.producto_id == producto_id
        )
        return self.session.exec(statement).all()

    def get_by_categoria(self, categoria_id: int) -> list[ProductoCategoria]:
        statement = select(ProductoCategoria).where(
            ProductoCategoria.categoria_id == categoria_id
        )
        return self.session.exec(statement).all()

    def delete(self, producto_id: int, categoria_id: int) -> None:
        link = self.session.get(ProductoCategoria, (producto_id, categoria_id))
        if not link:
            raise ValueError(
                f"No existe vínculo entre producto {producto_id} y categoría {categoria_id}"
            )
        self.session.delete(link)
        self.session.flush()
