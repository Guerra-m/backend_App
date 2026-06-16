from datetime import date
from typing import Annotated
from fastapi import APIRouter, Depends, Query

from app.core.deps import require_role
from app.modules.estadisticas.estadisticas_service import EstadisticasService
from app.modules.estadisticas.estadistitcas_schema import (
    ResumenKPIsResponse,
    VentasPeriodoItem,
    ProductoTopItem,
    PedidosEstadoItem,
    IngresoFormaPagoItem,
)

estadisticas_router = APIRouter(
    prefix="/api/v1/estadisticas",
    tags=["Estadísticas"],
    dependencies=[Depends(require_role(["ADMIN"]))],
)


def get_service() -> EstadisticasService:
    return EstadisticasService()


@estadisticas_router.get("/resumen", response_model=ResumenKPIsResponse)
def resumen_kpis(service: EstadisticasService = Depends(get_service)):
    """KPIs generales: ventas hoy, ticket promedio, pedidos activos, ingresos mes."""
    return service.get_resumen()


@estadisticas_router.get("/ventas", response_model=list[VentasPeriodoItem])
def ventas_por_periodo(
    desde: Annotated[date, Query(description="Fecha inicio (YYYY-MM-DD)")],
    hasta: Annotated[date, Query(description="Fecha fin (YYYY-MM-DD)")],
    agrupacion: Annotated[str, Query(description="day | week | month")] = "day",
    service: EstadisticasService = Depends(get_service),
):
    """Ventas agrupadas por período. Excluye pedidos CANCELADOS"""
    return service.get_ventas_periodo(desde, hasta, agrupacion)


@estadisticas_router.get("/productos-top", response_model=list[ProductoTopItem])
def productos_top(
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    service: EstadisticasService = Depends(get_service),
):
    """Top productos por ingresos. Usa subtotal_snap"""
    return service.get_productos_top(limit)


@estadisticas_router.get("/pedidos-por-estado", response_model=list[PedidosEstadoItem])
def pedidos_por_estado(service: EstadisticasService = Depends(get_service)):
    """Distribución de pedidos por estado actual."""
    return service.get_pedidos_por_estado()


@estadisticas_router.get("/ingresos", response_model=list[IngresoFormaPagoItem])
def ingresos_por_forma_pago(
    desde: Annotated[date, Query(description="Fecha inicio (YYYY-MM-DD)")],
    hasta: Annotated[date, Query(description="Fecha fin (YYYY-MM-DD)")],
    service: EstadisticasService = Depends(get_service),
):
    """Ingresos por forma de pago. Solo pagos approved"""
    return service.get_ingresos_por_forma_pago(desde, hasta)