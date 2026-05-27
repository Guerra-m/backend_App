<<<<<<< HEAD
=======

>>>>>>> 85d6e81cf8f66b9e8dae3a009360169a3d10b677
import json
from fastapi import HTTPException, status

from app.modules.pedido.pedido_uow import PedidoUnitOfWork
from app.modules.pedido.pedido_model import Pedido
from app.modules.pedido.pedido_schema import PedidoCreate, PedidoRead, PedidoReadDetalle
from app.modules.detalle_pedido.detalle_pedido_model import DetallePedido
from app.modules.detalle_pedido.detalle_pedido_schema import DetallePedidoRead
from app.modules.historial_estado_pedido.historial_estado_pedido_model import HistorialEstadoPedido
from app.modules.historial_estado_pedido.historial_estado_pedido_schema import HistorialEstadoPedidoRead
from app.modules.usuario.usuario_schema import UsuarioAuth

# ─── FSM ─────────────────────────────────────────────────────────────────────

FSM_TRANSITIONS: dict[str, list[str]] = {
    "PENDIENTE":  ["CONFIRMADO", "CANCELADO"],
    "CONFIRMADO": ["EN_PREP", "CANCELADO"],
    "EN_PREP":    ["EN_CAMINO", "CANCELADO"],
    "EN_CAMINO":  ["ENTREGADO", "CANCELADO"],
    "ENTREGADO":  [],
    "CANCELADO":  [],
}

# Estados desde los que CLIENT puede cancelar
CLIENT_CANCEL_STATES = ["PENDIENTE", "CONFIRMADO"]
# Estados desde los que solo ADMIN/PEDIDOS pueden cancelar
ADMIN_ONLY_CANCEL_FROM = ["EN_PREP", "EN_CAMINO"]


class PedidoService:

    def __init__(self, uow: PedidoUnitOfWork):
        self.uow = uow

    # ─── Crear pedido ─────────────────────────────────────────────────────────

    def crear_pedido(self, data: PedidoCreate, current_user: UsuarioAuth) -> PedidoRead:
        with self.uow as uow:
            # Validar forma de pago habilitada
            forma_pago = uow.formas_pago.get_by_id(data.forma_pago_codigo)
            if not forma_pago or not forma_pago.habilitado:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Forma de pago '{data.forma_pago_codigo}' no disponible",
                )

            # Validar dirección pertenece al usuario (si se envió)
            if data.direccion_id is not None:
                direccion = uow.direcciones.get_by_id(data.direccion_id)
                if not direccion or direccion.usuario_id != current_user.id:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Dirección no encontrada",
                    )

            # Procesar ítems — capturar snapshots
            subtotal = float("0.00")
            detalles_data = []

            for item in data.items:
                try:
                    producto = uow.productos.get_by_id(item.producto_id)
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Producto {item.producto_id} no encontrado",
                    )
                if not producto.disponible or producto.stock_cantidad <= 0:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Producto '{producto.nombre}' no disponible",
                    )

                precio_snap = producto.precio_base
                subtotal_snap = precio_snap * item.cantidad
                subtotal += subtotal_snap

                detalles_data.append({
                    "producto_id": item.producto_id,
                    "cantidad": item.cantidad,
                    "nombre_snapshot": producto.nombre,
                    "precio_snapshot": precio_snap,
                    "subtotal_snap": subtotal_snap,
                    "personalizacion": json.dumps(item.personalizacion) if item.personalizacion else None,
                })

            # Calcular total
            total = subtotal - data.descuento + data.costo_envio
            if total < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El total no puede ser negativo",
                )

            # Crear Pedido
            pedido = Pedido(
                usuario_id=current_user.id,
                direccion_id=data.direccion_id,
                estado_codigo="PENDIENTE",
                forma_pago_codigo=data.forma_pago_codigo,
                subtotal=subtotal,
                descuento=data.descuento,
                costo_envio=data.costo_envio,
                total=total,
                notas=data.notas,
            )
            pedido = uow.pedidos.add(pedido)

            # Crear DetallePedido
            for d in detalles_data:
                detalle = DetallePedido(pedido_id=pedido.id, **d)
                uow.detalles.add(detalle)

            # Registrar en historial (estado_desde=NULL = creación)
            uow.historial.add(HistorialEstadoPedido(
                pedido_id=pedido.id,
                estado_desde=None,
                estado_hacia="PENDIENTE",
                usuario_id=current_user.id,
                motivo="Pedido creado",
            ))

            return PedidoRead.model_validate(pedido)

    # ─── Listar pedidos ───────────────────────────────────────────────────────

    def listar_pedidos(
        self, current_user: UsuarioAuth, offset: int = 0, limit: int = 20
    ) -> list[PedidoRead]:
        with self.uow as uow:
            # CLIENT ve solo los suyos; ADMIN/PEDIDOS ven todos
            if "ADMIN" in current_user.roles or "PEDIDOS" in current_user.roles:
                pedidos = uow.pedidos.get_all_activos(offset=offset, limit=limit)
            else:
                pedidos = uow.pedidos.get_by_usuario(
                    current_user.id, offset=offset, limit=limit
                )
            return [PedidoRead.model_validate(p) for p in pedidos]

    # ─── Obtener pedido con detalle ───────────────────────────────────────────

    def obtener_pedido(self, pedido_id: int, current_user: UsuarioAuth) -> PedidoReadDetalle:
        with self.uow as uow:
            pedido = uow.pedidos.get_by_id_activo(pedido_id)
            if not pedido:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")

            # CLIENT solo puede ver sus propios pedidos
            if "ADMIN" not in current_user.roles and "PEDIDOS" not in current_user.roles:
                if pedido.usuario_id != current_user.id:
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin permisos")

            detalles = uow.detalles.get_by_pedido(pedido_id)
            historial = uow.historial.get_by_pedido(pedido_id)

            result = PedidoReadDetalle.model_validate(pedido)
            result.detalles = [DetallePedidoRead.model_validate(d) for d in detalles]
            result.historial = [HistorialEstadoPedidoRead.model_validate(h) for h in historial]
            return result

    # ─── Avanzar estado (FSM) ─────────────────────────────────────────────────

    def avanzar_estado(
        self,
        pedido_id: int,
        estado_hacia: str,
        current_user: UsuarioAuth,
        motivo: str | None = None,
    ) -> PedidoRead:
        with self.uow as uow:
            pedido = uow.pedidos.get_by_id_activo(pedido_id)
            if not pedido:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")

            estado_actual = pedido.estado_codigo
            transiciones_validas = FSM_TRANSITIONS.get(estado_actual, [])

            # Validar transición existe en FSM
            if estado_hacia not in transiciones_validas:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Transición inválida: {estado_actual} → {estado_hacia}",
                )

            # Validar permisos para cancelar desde estados avanzados
            if estado_hacia == "CANCELADO" and estado_actual in ADMIN_ONLY_CANCEL_FROM:
                if "ADMIN" not in current_user.roles and "PEDIDOS" not in current_user.roles:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Solo ADMIN/PEDIDOS pueden cancelar desde {estado_actual}",
                    )

            # CLIENT solo puede cancelar, desde PENDIENTE o CONFIRMADO
            if "ADMIN" not in current_user.roles and "PEDIDOS" not in current_user.roles:
                if estado_hacia != "CANCELADO":
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Los clientes solo pueden cancelar pedidos",
                    )
                if pedido.usuario_id != current_user.id:
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin permisos")

            # Validar motivo obligatorio al cancelar
            if estado_hacia == "CANCELADO" and not motivo:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El motivo es obligatorio al cancelar",
                )

            # Aplicar transición
            pedido = uow.pedidos.actualizar_estado(pedido, estado_hacia)

            # Registrar en historial (append-only)
            uow.historial.add(HistorialEstadoPedido(
                pedido_id=pedido.id,
                estado_desde=estado_actual,
                estado_hacia=estado_hacia,
                usuario_id=current_user.id,
                motivo=motivo,
            ))

            return PedidoRead.model_validate(pedido)

    # ─── Historial ────────────────────────────────────────────────────────────

    def obtener_historial(
        self, pedido_id: int, current_user: UsuarioAuth
    ) -> list[HistorialEstadoPedidoRead]:
        with self.uow as uow:
            pedido = uow.pedidos.get_by_id_activo(pedido_id)
            if not pedido:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")

            if "ADMIN" not in current_user.roles and "PEDIDOS" not in current_user.roles:
                if pedido.usuario_id != current_user.id:
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin permisos")

            historial = uow.historial.get_by_pedido(pedido_id)
            return [HistorialEstadoPedidoRead.model_validate(h) for h in historial]
