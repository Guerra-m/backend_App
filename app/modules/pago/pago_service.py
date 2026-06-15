import uuid
import hmac
import hashlib
from fastapi import HTTPException, status

from app.modules.pago.pago_uow import PagoUnitOfWork
from app.modules.pago.pago_schema import PagoCreate, PagoUpdate, PagoRead
from app.modules.historial_estado_pedido.historial_estado_pedido_model import HistorialEstadoPedido
from app.modules.usuario.usuario_schema import UsuarioAuth

# Mapa de estados MP → EstadoPedido FSM
MP_STATUS_TO_PEDIDO: dict[str, str] = {
    "approved": "CONFIRMADO",
    "rejected": None, # no avanza el pedido
    "pending":  None, # espera webhook
    "in_process": None,
    "cancelled": "CANCELADO",
}


class PagoService:

    def __init__(self, uow: PagoUnitOfWork):
        self.uow = uow

    def crear_pago(
        self,
        pedido_id: int,
        transaction_amount: float,
        current_user: UsuarioAuth,
    ) -> PagoRead:
        
        #Crea el registro de Pago en BD con estado 'pending'.
        #El SDK de MercadoPago se llama en el router con el token de tarjeta.
        
        with self.uow as uow:
            # Validar que el pedido exista y pertenezca al usuario
            pedido = uow.pedidos.get_by_id_activo(pedido_id)
            if not pedido:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Pedido no encontrado",
                )
            if pedido.usuario_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Sin permisos sobre este pedido",
                )

            # Validar que no exista ya un pago para este pedido
            existente = uow.pagos.get_by_pedido(pedido_id)
            if existente:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Ya existe un pago registrado para este pedido",
                )

            # Generar claves únicas
            external_reference = str(uuid.uuid4())
            idempotency_key = str(uuid.uuid4())

            pago = uow.pagos.create(PagoCreate(
                pedido_id=pedido_id,
                external_reference=external_reference,
                idempotency_key=idempotency_key,
                transaction_amount=transaction_amount,
                mp_status="pending",
            ))

            return PagoRead.model_validate(pago)

    def obtener_pago_por_pedido(self, pedido_id: int, current_user: UsuarioAuth) -> PagoRead:
        with self.uow as uow:
            pedido = uow.pedidos.get_by_id_activo(pedido_id)
            if not pedido:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")

            # Solo el dueño o ADMIN puede ver el pago
            if "ADMIN" not in current_user.roles and pedido.usuario_id != current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin permisos")

            pago = uow.pagos.get_by_pedido(pedido_id)
            if not pago:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pago no encontrado")

            return PagoRead.model_validate(pago)

    def procesar_webhook(self, data: dict) -> dict:
        
        #Procesa notificación IPN de MercadoPago.
        #Actualiza estado del Pago y avanza el Pedido según FSM si aplica.
        with self.uow as uow:
            topic = data.get("topic") or data.get("type")
            if topic != "payment":
                return {"status": "ignored", "reason": "topic no es payment"}

            mp_payment_id = int(data.get("id") or data.get("data", {}).get("id", 0))
            if not mp_payment_id:
                return {"status": "ignored", "reason": "sin payment_id"}

            # Buscar pago por external_reference
            external_reference = data.get("external_reference")
            pago = uow.pagos.get_by_external_reference(external_reference) if external_reference else None

            if not pago:
                return {"status": "ignored", "reason": "pago no encontrado"}

            mp_status = data.get("status", "pending")
            mp_status_detail = data.get("status_detail")
            payment_method_id = data.get("payment_method_id")
            transaction_amount = data.get("transaction_amount", pago.transaction_amount)

            # Actualizar registro de pago
            uow.pagos.update(pago, PagoUpdate(
                mp_payment_id=mp_payment_id,
                mp_status=mp_status,
                mp_status_detail=mp_status_detail,
                payment_method_id=payment_method_id,
                transaction_amount=transaction_amount,
            ))

            # Avanzar estado del pedido si corresponde
            nuevo_estado_pedido = MP_STATUS_TO_PEDIDO.get(mp_status)
            if nuevo_estado_pedido:
                pedido = uow.pedidos.get_by_id_activo(pago.pedido_id)
                if pedido and pedido.estado_codigo == "PENDIENTE":
                    uow.pedidos.actualizar_estado(pedido, nuevo_estado_pedido)
                    uow.historial.add(HistorialEstadoPedido(
                        pedido_id=pedido.id,
                        estado_desde=pedido.estado_codigo,
                        estado_hacia=nuevo_estado_pedido,
                        usuario_id=None,  # actor = sistema (webhook)
                        motivo=f"Webhook MercadoPago: {mp_status}",
                    ))

            return {"status": "ok"}