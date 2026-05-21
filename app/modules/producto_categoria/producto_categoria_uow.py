from sqlmodel import Session
from app.core.database import engine
from app.modules.producto_categoria.producto_categoria_repository import ProductoCategoriaRepository
from app.modules.producto.producto_repository import ProductoRepository
from app.modules.categoria.categoria_repository import CategoriaRepository


class ProductoCategoriaUnitOfWork:
    def __enter__(self):
        self.session = Session(engine, expire_on_commit=False)
        self.producto_categorias = ProductoCategoriaRepository(self.session)
        self.productos = ProductoRepository(self.session)
        self.categorias = CategoriaRepository(self.session)
        return self

    def __exit__(self, exc_type, *args):
        if exc_type:
            self.session.rollback()
        else:
            self.session.commit()
        self.session.close()
