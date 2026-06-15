from datetime import datetime, timezone
from sqlmodel import Session, select
from app.core.base_repository import BaseRepository
from app.modules.pago.pago_model import Pago
from app.modules.pago.pago_schema import PagoCreate, PagoUpdate


class PagoRepository(BaseRepository[Pago]):

    def __init__(self, session: Session):
        super().__init__(Pago, session)

    def create(self, data: PagoCreate) -> Pago:
        pago = Pago(**data.model_dump())
        self.session.add(pago)
        self.session.flush()
        return pago

    def get_by_id(self, pago_id: int) -> Pago:
        pago = self.session.get(Pago, pago_id)
        if not pago:
            raise ValueError(f"Pago con id {pago_id} no encontrado")
        return pago

    def get_by_pedido(self, pedido_id: int) -> Pago | None:
        statement = select(Pago).where(Pago.pedido_id == pedido_id)
        return self.session.exec(statement).first()

    def get_by_external_reference(self, external_reference: str) -> Pago | None:
        statement = select(Pago).where(Pago.external_reference == external_reference)
        return self.session.exec(statement).first()

    def get_by_idempotency_key(self, idempotency_key: str) -> Pago | None:
        statement = select(Pago).where(Pago.idempotency_key == idempotency_key)
        return self.session.exec(statement).first()

    def update(self, pago: Pago, data: PagoUpdate) -> Pago:
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(pago, key, value)
        pago.updated_at = datetime.now(timezone.utc)
        self.session.add(pago)
        self.session.flush()
        return pago