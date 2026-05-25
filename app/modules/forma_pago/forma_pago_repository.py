from sqlmodel import Session, select
from app.core.base_repository import BaseRepository
from app.modules.forma_pago.forma_pago_model import FormaPago


class FormaPagoRepository(BaseRepository[FormaPago]):

    def __init__(self, session: Session):
        super().__init__(FormaPago, session)

    def get_habilitadas(self) -> list[FormaPago]:
        return list(self.session.exec(
            select(FormaPago).where(FormaPago.habilitado == True)
        ).all())
