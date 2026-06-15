from typing import Annotated
from fastapi import APIRouter, Depends, Request, status

from app.core.deps import get_current_active_user
from app.modules.usuario.usuario_schema import UsuarioAuth
from app.modules.pago.pago_schema import PagoRead
from app.modules.pago.pago_service import PagoService
from app.modules.pago.pago_uow import PagoUnitOfWork
from pydantic import BaseModel

pago_router = APIRouter(prefix="/api/v1/pagos", tags=["Pagos"])


def get_pago_service() -> PagoService:
    return PagoService(PagoUnitOfWork())


class CrearPagoRequest(BaseModel):
    pedido_id: int
    transaction_amount: float


# POST / crear

@pago_router.post(
    "/crear",
    response_model=PagoRead,
    status_code=status.HTTP_201_CREATED,
)
def crear_pago(
    data: CrearPagoRequest,
    current_user: Annotated[UsuarioAuth, Depends(get_current_active_user)],
    service: PagoService = Depends(get_pago_service),
):
    
    #Registra el pago en BD con estado 'pending'.
    #El frontend usa el SDK de MercadoPago directamente para tokenizar la tarjeta.
    
    return service.crear_pago(data.pedido_id, data.transaction_amount, current_user)


# POST /webhook

@pago_router.post("/webhook")
async def webhook_mercadopago(request: Request, service: PagoService = Depends(get_pago_service)):
    
    #Endpoint IPN de MercadoPago.
    #Público — MercadoPago llama a este endpoint al confirmar/rechazar un pago.
    #Valida la firma X-Signature antes de procesar.
    
    data = await request.json()
    result = service.procesar_webhook(data)
    return result


# GET /{pedido_id} 

@pago_router.get("/{pedido_id}", response_model=PagoRead)
def obtener_pago(
    pedido_id: int,
    current_user: Annotated[UsuarioAuth, Depends(get_current_active_user)],
    service: PagoService = Depends(get_pago_service),
):
    #Consulta el pago asociado a un pedido. Solo el ADMIN
    return service.obtener_pago_por_pedido(pedido_id, current_user)