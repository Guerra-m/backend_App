from typing import Optional
from datetime import date
from pydantic import BaseModel


class ResumenKPIsResponse(BaseModel):
    ventas_hoy: float
    ticket_promedio: float
    pedidos_activos: int
    ingresos_mes_actual: float


class VentasPeriodoItem(BaseModel):
    periodo: str
    total_ventas: float
    cantidad_pedidos: int


class ProductoTopItem(BaseModel):
    producto_id: int
    nombre: str
    cantidad_vendida: int
    ingresos: float


class PedidosEstadoItem(BaseModel):
    estado_codigo: str
    cantidad: int


class IngresoFormaPagoItem(BaseModel):
    forma_pago_codigo: str
    total: float
    cantidad_pedidos: int