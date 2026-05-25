from typing import Annotated
from fastapi import APIRouter, Depends
from sqlmodel import Session
from app.core.database import engine
from app.core.deps import get_current_active_user
from app.modules.usuario.usuario_schema import UsuarioAuth
from app.modules.forma_pago.forma_pago_schema import FormaPagoRead
from app.modules.forma_pago.forma_pago_repository import FormaPagoRepository

forma_pago_router = APIRouter(
    prefix="/api/v1/formas-pago", tags=["Formas de Pago"])


@forma_pago_router.get("/", response_model=list[FormaPagoRead])
def listar_formas_pago(
    _user: Annotated[UsuarioAuth, Depends(get_current_active_user)],
):
    with Session(engine) as session:
        repo = FormaPagoRepository(session)
        return [FormaPagoRead.model_validate(f) for f in repo.get_habilitadas()]
