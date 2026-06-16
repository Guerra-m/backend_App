from datetime import date, datetime, timezone
from sqlmodel import Session, select, func, text
from sqlalchemy import and_

from app.modules.pedido.pedido_model import Pedido
from app.modules.detalle_pedido.detalle_pedido_model import DetallePedido
from app.modules.pago.pago_model import Pago


class EstadisticasRepository:

    def __init__(self, session: Session):
        self.session = session

    def get_resumen_kpis(self) -> dict:
        """KPIs generales: ventas hoy, ticket promedio, pedidos activos, ingresos mes."""
        hoy = datetime.now(timezone.utc).date()
        inicio_mes = hoy.replace(day=1)

        # Ventas hoy — solo pedidos no cancelados
        ventas_hoy = self.session.exec(
            select(func.coalesce(func.sum(Pedido.total), 0)).where(
                func.date(Pedido.created_at) == hoy,
                Pedido.estado_codigo != "CANCELADO",
                Pedido.deleted_at == None,
            )
        ).one()

        # Ticket promedio — total / cantidad de pedidos no cancelados
        stats = self.session.exec(
            select(
                func.coalesce(func.avg(Pedido.total), 0),
            ).where(
                Pedido.estado_codigo != "CANCELADO",
                Pedido.deleted_at == None,
            )
        ).one()

        # Pedidos activos (no terminales)
        pedidos_activos = self.session.exec(
            select(func.count(Pedido.id)).where(
                Pedido.estado_codigo.in_(["PENDIENTE", "CONFIRMADO", "EN_PREP"]),
                Pedido.deleted_at == None,
            )
        ).one()

        # Ingresos mes actual — solo pagos approved
        ingresos_mes = self.session.exec(
            select(func.coalesce(func.sum(Pedido.total), 0)).where(
                func.date(Pedido.created_at) >= inicio_mes,
                Pedido.estado_codigo != "CANCELADO",
                Pedido.deleted_at == None,
            )
        ).one()

        return {
            "ventas_hoy": float(ventas_hoy),
            "ticket_promedio": float(stats),
            "pedidos_activos": int(pedidos_activos),
            "ingresos_mes_actual": float(ingresos_mes),
        }

    def get_ventas_periodo(self, desde: date, hasta: date, agrupacion: str = "day") -> list[dict]:
        """Ventas agrupadas por día, semana o mes. EST-01: excluye CANCELADO."""
        # Validar agrupacion
        if agrupacion not in ("day", "week", "month"):
            agrupacion = "day"

        # Usar text() para DATE_TRUNC de PostgreSQL
        periodo_col = func.to_char(
            func.date_trunc(agrupacion, Pedido.created_at),
            "YYYY-MM-DD" if agrupacion == "day" else ("YYYY-IW" if agrupacion == "week" else "YYYY-MM")
        )

        rows = self.session.exec(
            select(
                periodo_col.label("periodo"),
                func.coalesce(func.sum(Pedido.total), 0).label("total_ventas"),
                func.count(Pedido.id).label("cantidad_pedidos"),
            ).where(
                func.date(Pedido.created_at) >= desde,
                func.date(Pedido.created_at) <= hasta,
                Pedido.estado_codigo != "CANCELADO",
                Pedido.deleted_at == None,
            ).group_by("periodo")
            .order_by("periodo")
        ).all()

        return [
            {
                "periodo": str(r[0]),
                "total_ventas": float(r[1]),
                "cantidad_pedidos": int(r[2]),
            }
            for r in rows
        ]

    def get_productos_top(self, limit: int = 10) -> list[dict]:
        """Top productos por ingresos. EST-02: usa subtotal_snap."""
        rows = self.session.exec(
            select(
                DetallePedido.producto_id,
                DetallePedido.nombre_snapshot,
                func.sum(DetallePedido.cantidad).label("cantidad_vendida"),
                func.sum(DetallePedido.subtotal_snap).label("ingresos"),
            )
            .join(Pedido, Pedido.id == DetallePedido.pedido_id)
            .where(
                Pedido.estado_codigo != "CANCELADO",
                Pedido.deleted_at == None,
            )
            .group_by(DetallePedido.producto_id, DetallePedido.nombre_snapshot)
            .order_by(func.sum(DetallePedido.subtotal_snap).desc())
            .limit(limit)
        ).all()

        return [
            {
                "producto_id": r[0],
                "nombre": r[1],
                "cantidad_vendida": int(r[2]),
                "ingresos": float(r[3]),
            }
            for r in rows
        ]

    def get_pedidos_por_estado(self) -> list[dict]:
        """Distribución de pedidos por estado actual."""
        rows = self.session.exec(
            select(
                Pedido.estado_codigo,
                func.count(Pedido.id).label("cantidad"),
            )
            .where(Pedido.deleted_at == None)
            .group_by(Pedido.estado_codigo)
        ).all()

        return [
            {"estado_codigo": r[0], "cantidad": int(r[1])}
            for r in rows
        ]

    def get_ingresos_por_forma_pago(self, desde: date, hasta: date) -> list[dict]:
        """Ingresos por forma de pago. EST-03: solo pagos approved."""
        rows = self.session.exec(
            select(
                Pedido.forma_pago_codigo,
                func.coalesce(func.sum(Pedido.total), 0).label("total"),
                func.count(Pedido.id).label("cantidad_pedidos"),
            )
            .join(Pago, Pago.pedido_id == Pedido.id)
            .where(
                func.date(Pedido.created_at) >= desde,
                func.date(Pedido.created_at) <= hasta,
                Pedido.estado_codigo != "CANCELADO",
                Pedido.deleted_at == None,
                Pago.mp_status == "approved",
            )
            .group_by(Pedido.forma_pago_codigo)
            .order_by(func.sum(Pedido.total).desc())
        ).all()

        return [
            {
                "forma_pago_codigo": r[0],
                "total": float(r[1]),
                "cantidad_pedidos": int(r[2]),
            }
            for r in rows
        ]