from sqlmodel import Session
from app.core.database import engine
from app.modules.categoria.categoria_repository import CategoriaRepository


class CategoriaUnitOfWork:
    def __enter__(self):
        self.session = Session(engine, expire_on_commit=False)
        self.categorias = CategoriaRepository(self.session)
        return self

    def __exit__(self, exc_type, *args):
        if exc_type:
            self.session.rollback()
        else:
            self.session.commit()
        self.session.close()
