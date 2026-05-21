from sqlmodel import Session
from app.core.database import engine
from app.modules.producto.producto_repository import ProductoRepository
from app.modules.producto_categoria.producto_categoria_repository import ProductoCategoriaRepository
from app.modules.producto_ingrediente.producto_ingrediente_repository import ProductoIngredienteRepository


class ProductoUnitOfWork:
    
    #Agrupa en una sola transacción las operaciones sobre Producto
    #y sus tablas intermedias ProductoCategoria y ProductoIngrediente.
    #Por eso el uso de los 3 repository
    
    def __enter__(self):
        self.session = Session(engine, expire_on_commit=False)
        self.productos = ProductoRepository(self.session)
        self.producto_categorias = ProductoCategoriaRepository(self.session)
        self.producto_ingredientes = ProductoIngredienteRepository(self.session)
        return self

    def __exit__(self, exc_type, *args):
        if exc_type:
            self.session.rollback()
        else:
            self.session.commit()
        self.session.close()
