from datetime import date
from sqlmodel import Session
from app.core.database import engine
from app.modules.estadisticas.estadisticas_repository import EstadisticasRepository
from app.modules.estadisticas.estadistitcas_schema import (
    ResumenKPIsResponse,
    VentasPeriodoItem,
    ProductoTopItem,
    PedidosEstadoItem,
    IngresoFormaPagoItem,
)


class EstadisticasService:

    def get_resumen(self) -> ResumenKPIsResponse:
        with Session(engine) as session:
            repo = EstadisticasRepository(session)
            data = repo.get_resumen_kpis()
            return ResumenKPIsResponse(**data)

    def get_ventas_periodo(
        self, desde: date, hasta: date, agrupacion: str = "day"
    ) -> list[VentasPeriodoItem]:
        with Session(engine) as session:
            repo = EstadisticasRepository(session)
            rows = repo.get_ventas_periodo(desde, hasta, agrupacion)
            return [VentasPeriodoItem(**r) for r in rows]

    def get_productos_top(self, limit: int = 10) -> list[ProductoTopItem]:
        with Session(engine) as session:
            repo = EstadisticasRepository(session)
            rows = repo.get_productos_top(limit)
            return [ProductoTopItem(**r) for r in rows]

    def get_pedidos_por_estado(self) -> list[PedidosEstadoItem]:
        with Session(engine) as session:
            repo = EstadisticasRepository(session)
            rows = repo.get_pedidos_por_estado()
            return [PedidosEstadoItem(**r) for r in rows]

    def get_ingresos_por_forma_pago(
        self, desde: date, hasta: date
    ) -> list[IngresoFormaPagoItem]:
        with Session(engine) as session:
            repo = EstadisticasRepository(session)
            rows = repo.get_ingresos_por_forma_pago(desde, hasta)
            return [IngresoFormaPagoItem(**r) for r in rows]