from sqlmodel import Session, select
from app.modules.producto_ingrediente.producto_ingrediente_model import ProductoIngrediente
from app.modules.producto_ingrediente.producto_ingrediente_schema import ProductoIngredienteCreate


class ProductoIngredienteRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, data: ProductoIngredienteCreate) -> ProductoIngrediente:
        existing = self.session.get(
            ProductoIngrediente, (data.producto_id, data.ingrediente_id)
        )
        if existing:
            raise ValueError(
                f"El producto {data.producto_id} ya tiene vinculado el ingrediente {data.ingrediente_id}"
            )
        link = ProductoIngrediente(**data.model_dump())
        self.session.add(link)
        self.session.flush()
        return link

    def get_by_producto(self, producto_id: int) -> list[ProductoIngrediente]:
        statement = select(ProductoIngrediente).where(
            ProductoIngrediente.producto_id == producto_id
        )
        return self.session.exec(statement).all()

    def get_by_ingrediente(self, ingrediente_id: int) -> list[ProductoIngrediente]:
        statement = select(ProductoIngrediente).where(
            ProductoIngrediente.ingrediente_id == ingrediente_id
        )
        return self.session.exec(statement).all()

    def delete(self, producto_id: int, ingrediente_id: int) -> None:
        link = self.session.get(ProductoIngrediente, (producto_id, ingrediente_id))
        if not link:
            raise ValueError(
                f"No existe vínculo entre producto {producto_id} e ingrediente {ingrediente_id}"
            )
        self.session.delete(link)
        self.session.flush()
