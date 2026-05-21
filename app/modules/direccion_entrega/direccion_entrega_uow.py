from sqlmodel import Session
from app.core.database import engine
from app.modules.direccion_entrega.direccion_entrega_repository import DireccionEntregaRepository

class DireccionEntregaUnitOfWork:

    def __enter__(self):
        self.session = Session(engine, expire_on_commit=False)
        self.direcciones = DireccionEntregaRepository(self.session)
        return self

    def __exit__(self, exc_type, *args):
        if exc_type:
            self.session.rollback()
        else:
            self.session.commit()
        self.session.close()
