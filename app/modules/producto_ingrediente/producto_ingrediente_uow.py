from sqlmodel import Session
from app.core.database import engine
from app.modules.producto_ingrediente.producto_ingrediente_repository import ProductoIngredienteRepository
from app.modules.producto.producto_repository import ProductoRepository
from app.modules.ingrediente.ingrediente_repository import IngredienteRepository


class ProductoIngredienteUnitOfWork:
    def __enter__(self):
        self.session = Session(engine, expire_on_commit=False)
        self.producto_ingredientes = ProductoIngredienteRepository(self.session)
        self.productos = ProductoRepository(self.session)
        self.ingredientes = IngredienteRepository(self.session)
        return self

    def __exit__(self, exc_type, *args):
        if exc_type:
            self.session.rollback()
        else:
            self.session.commit()
        self.session.close()
