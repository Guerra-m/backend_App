from sqlmodel import Session
from app.core.database import engine
from app.modules.unidad_medida.unidad_medida_repository import UnidadMedidaRepository
 
 
class UnidadMedidaUnitOfWork:
 
    def __enter__(self):
        self.session = Session(engine, expire_on_commit=False)
        self.unidades = UnidadMedidaRepository(self.session)
        return self
 
    def __exit__(self, exc_type, *args):
        if exc_type:
            self.session.rollback()
        else:
            self.session.commit()
        self.session.close()