from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, field_validator

from app.modules.categoria.categoria_schema import CategoriaRead
from app.modules.ingrediente.ingrediente_schema import IngredienteRead
from app.modules.unidad_medida.unidad_medida_schema import UnidadMedidaRead


class ProductoCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    precio_base: float
    imagenes_url: Optional[List[str]] = None
    unidad_venta_id: Optional[int] = None
    stock_cantidad: int = 0
    disponible: bool = True

    @field_validator("precio_base")
    @classmethod
    def precio_no_negativo(cls, v):
        if v < 0:
            raise ValueError("El precio base no puede ser negativo")
        return v

    @field_validator("stock_cantidad")
    @classmethod
    def stock_no_negativo(cls, v):
        if v < 0:
            raise ValueError("El stock no puede ser negativo")
        return v


class ProductoUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    precio_base: Optional[float] = None
    imagenes_url: Optional[List[str]] = None
    unidad_venta_id: Optional[int] = None
    stock_cantidad: Optional[int] = None
    disponible: Optional[bool] = None

class ImagenProductoUpdate(BaseModel):
    """PATCH /productos/{id}/imagenes — reemplaza el array completo."""
    imagenes_url: List[str]


class ProductoRead(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str]
    precio_base: float
    imagenes_url: Optional[List[str]]
    unidad_venta_id: Optional[int]
    stock_cantidad: int
    disponible: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("imagenes_url", mode="before")
    @classmethod
    def parse_imagenes_url(cls, v):
        if v is None:
            return None
        if isinstance(v, list):
            # Filtrar cualquier elemento que no sea string válido (caracteres sueltos, etc.)
            strings = [s for s in v if isinstance(s, str) and len(s) > 3]
            return strings if strings else None
        if isinstance(v, str):
            s = v.strip()
            if not s or s in ("{}", "{}"):
                return None
            # Formato crudo PostgreSQL: {"url1","url2"}
            if s.startswith("{") and s.endswith("}"):
                content = s[1:-1]
                return [item.strip('"') for item in content.split(",") if item.strip()]
            return [s]
        return v


class ProductoReadDetalle(ProductoRead):
    #Para mostrar producto con sus categorías e ingredientes para respuestas completas
    categorias: List[dict] = []
    ingredientes: List[dict] = []

    model_config = {"from_attributes": True}

class ProductoReadConRelaciones(ProductoRead):
    categorias: list[CategoriaRead] = []
    ingredientes: list[IngredienteRead] = []

    unidad_venta: Optional[UnidadMedidaRead] = None
 
    model_config = {"from_attributes": True}