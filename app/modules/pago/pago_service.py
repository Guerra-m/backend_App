import uuid
import mercadopago
from fastapi import HTTPException, status

from app.core.config import settings
from app.modules.pago.pago_uow import PagoUnitOfWork
from app.modules.pago.pago_schema import PagoCreate, PagoUpdate, PagoRead
from app.modules.historial_estado_pedido.historial_estado_pedido_model import HistorialEstadoPedido
from app.modules.usuario.usuario_schema import UsuarioAuth

MP_STATUS_TO_PEDIDO: dict[str, str | None] = {
    "approved":   "CONFIRMADO",
    "rejected":   None,
    "pending":    None,
    "in_process": None,
    "cancelled":  "CANCELADO",
}


def _get_sdk() -> mercadopago.SDK:
    return mercadopago.SDK(settings.mp_access_token)


class PagoService:

    def __init__(self, uow: PagoUnitOfWork):
        self.uow = uow

    # ─── Crear pago (pending) ─────────────────────────────────────────────────

    def crear_pago(
        self,
        pedido_id: int,
        transaction_amount: float,
        current_user: UsuarioAuth,
    ) -> PagoRead:
        with self.uow as uow:
            pedido = uow.pedidos.get_by_id_activo(pedido_id)
            if not pedido:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")
            if pedido.usuario_id != current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin permisos sobre este pedido")

            existente = uow.pagos.get_by_pedido(pedido_id)
            if existente:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya existe un pago para este pedido")

            pago = uow.pagos.create(PagoCreate(
                pedido_id=pedido_id,
                external_reference=str(uuid.uuid4()),
                idempotency_key=str(uuid.uuid4()),
                transaction_amount=transaction_amount,
                mp_status="pending",
            ))
            return PagoRead.model_validate(pago)

    # ─── Crear preferencia MP (genera init_point) ─────────────────────────────

    def crear_preferencia(self, pedido_id: int, current_user: UsuarioAuth) -> dict:
        with self.uow as uow:
            pago = uow.pagos.get_by_pedido(pedido_id)
            if not pago:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Creá el pago antes de generar la preferencia")

            pedido = uow.pedidos.get_by_id_activo(pedido_id)
            if not pedido:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")
            if pedido.usuario_id != current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin permisos")

        sdk = _get_sdk()
        preference_data = {
    "items": [{
        "title": f"Pedido #{pedido_id}",
        "quantity": 1,
        "unit_price": float(pedido.total),
        "currency_id": "ARS",
    }],
    "external_reference": pago.external_reference,
    "notification_url": f"{settings.mp_ngrok_url}/api/v1/pagos/webhook",
    "back_urls": {
        "success": f"{settings.mp_ngrok_url}/pago/exito",
        "failure": f"{settings.mp_ngrok_url}/pago/fallo",
        "pending": f"{settings.mp_ngrok_url}/pago/pendiente",
    },
    "auto_return": "approved",
}
        response = sdk.preference().create(preference_data)

        # ─── DEBUG TEMPORAL ───────────────────────────────────────────────
        print("MP RESPONSE STATUS:", response["status"])
        print("MP RESPONSE BODY:", response.get("response"))
        # ─────────────────────────────────────────────────────────────────

        if response["status"] != 201:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Error al crear preferencia MP: {response.get('response')}",
            )

        return {
            "init_point": response["response"]["init_point"],
            "preference_id": response["response"]["id"],
        }

    # ─── Obtener pago ─────────────────────────────────────────────────────────

    def obtener_pago_por_pedido(self, pedido_id: int, current_user: UsuarioAuth) -> PagoRead:
        with self.uow as uow:
            pedido = uow.pedidos.get_by_id_activo(pedido_id)
            if not pedido:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")
            if "ADMIN" not in current_user.roles and pedido.usuario_id != current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin permisos")

            pago = uow.pagos.get_by_pedido(pedido_id)
            if not pago:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pago no encontrado")
            return PagoRead.model_validate(pago)

    # ─── Procesar webhook MP ──────────────────────────────────────────────────

    def procesar_webhook(self, payment_data: dict) -> dict:
        with self.uow as uow:
            external_reference = payment_data.get("external_reference")
            pago = uow.pagos.get_by_external_reference(external_reference) if external_reference else None
            if not pago:
                return {"status": "ignored", "reason": "pago no encontrado por external_reference"}

            mp_status = payment_data.get("status", "pending")

            uow.pagos.update(pago, PagoUpdate(
                mp_payment_id=payment_data.get("id"),
                mp_status=mp_status,
                mp_status_detail=payment_data.get("status_detail"),
                payment_method_id=payment_data.get("payment_method_id"),
                transaction_amount=payment_data.get("transaction_amount", pago.transaction_amount),
            ))

            nuevo_estado_pedido = MP_STATUS_TO_PEDIDO.get(mp_status)
            resultado: dict = {"status": "ok"}

            if nuevo_estado_pedido:
                pedido = uow.pedidos.get_by_id_activo(pago.pedido_id)
                if pedido and pedido.estado_codigo == "PENDIENTE":
                    estado_actual = pedido.estado_codigo
                    uow.pedidos.actualizar_estado(pedido, nuevo_estado_pedido)
                    uow.historial.add(HistorialEstadoPedido(
                        pedido_id=pedido.id,
                        estado_desde=estado_actual,
                        estado_hacia=nuevo_estado_pedido,
                        usuario_id=None,
                        motivo=f"Webhook MercadoPago: {mp_status}",
                    ))
                    resultado["pedido_id"] = pedido.id
                    resultado["nuevo_estado"] = nuevo_estado_pedido

            return resultado