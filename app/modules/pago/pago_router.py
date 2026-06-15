import hmac
import hashlib
from typing import Annotated

import mercadopago
from fastapi import APIRouter, Depends, Request, HTTPException, status
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel

from app.core.config import settings
from app.core.deps import get_current_active_user
from app.core.ws_manager import manager
from app.modules.usuario.usuario_schema import UsuarioAuth
from app.modules.pago.pago_schema import PagoRead
from app.modules.pago.pago_service import PagoService
from app.modules.pago.pago_uow import PagoUnitOfWork

pago_router = APIRouter(prefix="/api/v1/pagos", tags=["Pagos"])


def get_pago_service() -> PagoService:
    return PagoService(PagoUnitOfWork())


# ─── Schemas locales ──────────────────────────────────────────────────────────

class CrearPagoRequest(BaseModel):
    pedido_id: int
    transaction_amount: float


class CrearPreferenciaRequest(BaseModel):
    pedido_id: int


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _validate_mp_signature(x_signature: str, x_request_id: str, payment_id: int) -> None:
    """Valida el header X-Signature de MercadoPago. Si no hay secret configurado, omite."""
    if not settings.mp_webhook_secret:
        return

    ts = v1 = ""
    for part in x_signature.split(","):
        key, _, val = part.partition("=")
        key = key.strip()
        if key == "ts":
            ts = val.strip()
        elif key == "v1":
            v1 = val.strip()

    if not ts or not v1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Firma MP malformada")

    message = f"id:{payment_id};request-id:{x_request_id};ts:{ts};"
    expected = hmac.new(
        settings.mp_webhook_secret.encode(),
        message.encode(),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected, v1):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Firma MP inválida")


# ─── Endpoints ────────────────────────────────────────────────────────────────

@pago_router.post("/crear", response_model=PagoRead, status_code=status.HTTP_201_CREATED)
def crear_pago(
    data: CrearPagoRequest,
    current_user: Annotated[UsuarioAuth, Depends(get_current_active_user)],
    service: PagoService = Depends(get_pago_service),
):
    return service.crear_pago(data.pedido_id, data.transaction_amount, current_user)


@pago_router.post("/crear-preferencia")
def crear_preferencia(
    data: CrearPreferenciaRequest,
    current_user: Annotated[UsuarioAuth, Depends(get_current_active_user)],
    service: PagoService = Depends(get_pago_service),
):
    """Genera la preferencia de pago en MP y devuelve el init_point (URL de checkout)."""
    return service.crear_preferencia(data.pedido_id, current_user)


@pago_router.post("/webhook")
async def webhook_mercadopago(
    request: Request,
    service: PagoService = Depends(get_pago_service),
):
    """
    Endpoint IPN de MercadoPago (público).
    MP llama aquí al confirmar/rechazar un pago.
    """
    body = await request.json()

    # Ignorar notificaciones que no sean de pagos
    topic = body.get("type") or body.get("topic")
    if topic != "payment":
        return {"status": "ignored", "reason": "topic != payment"}

    payment_id = int((body.get("data") or {}).get("id") or body.get("id") or 0)
    if not payment_id:
        return {"status": "ignored", "reason": "sin payment_id"}

    # Validar firma
    x_signature = request.headers.get("x-signature", "")
    x_request_id = request.headers.get("x-request-id", "")
    _validate_mp_signature(x_signature, x_request_id, payment_id)

    # Obtener datos reales del pago desde la API de MP
    sdk = mercadopago.SDK(settings.mp_access_token)
    mp_response = await run_in_threadpool(sdk.payment().get, payment_id)

    if mp_response.get("status") != 200:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="No se pudo obtener el pago de MP")

    payment_data: dict = mp_response["response"]

    # Procesar en el service
    result = service.procesar_webhook(payment_data)

    # Broadcast WebSocket si el pedido cambió de estado
    if result.get("pedido_id") and result.get("nuevo_estado"):
        ws_message = {
            "type": "estado_actualizado",
            "pedido_id": result["pedido_id"],
            "estado_hacia": result["nuevo_estado"],
        }
        await manager.broadcast_all(ws_message)
        await manager.broadcast_pedido(result["pedido_id"], ws_message)

    return {"status": "ok"}


@pago_router.get("/{pedido_id}", response_model=PagoRead)
def obtener_pago(
    pedido_id: int,
    current_user: Annotated[UsuarioAuth, Depends(get_current_active_user)],
    service: PagoService = Depends(get_pago_service),
):
    return service.obtener_pago_por_pedido(pedido_id, current_user)
