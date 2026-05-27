

from fastapi import FastAPI
from app.core.database import create_db_and_tables
from contextlib import asynccontextmanager

from fastapi.middleware.cors import CORSMiddleware

# Importar todos los modelos para que SQLModel los registre antes de crear las tablas
from app.modules.rol.rol_model import Rol                                          
from app.modules.usuario.usuario_model import Usuario
from app.modules.usuario_rol.usuario_rol_model import UsuarioRol                    
from app.modules.direccion_entrega.direccion_entrega_model import DireccionEntrega
from app.modules.refresh_token.refresh_token_model import RefreshToken

from app.modules.forma_pago.forma_pago_model import FormaPago
from app.modules.estado_pedido.estado_pedido_model import EstadoPedido
from app.modules.pedido.pedido_model import Pedido
from app.modules.detalle_pedido.detalle_pedido_model import DetallePedido
from app.modules.historial_estado_pedido.historial_estado_pedido_model import HistorialEstadoPedido

from app.modules.categoria.categoria_model import Categoria
from app.modules.ingrediente.ingrediente_model import Ingrediente
from app.modules.producto.producto_model import Producto
from app.modules.producto_categoria.producto_categoria_model import ProductoCategoria
from app.modules.producto_ingrediente.producto_ingrediente_model import ProductoIngrediente

# Importar routers
from app.modules.usuario.usuario_router import usuario_router
from app.modules.usuario_rol.usuario_rol_router import usuario_rol_router
from app.modules.rol.rol_router import rol_router
from app.modules.direccion_entrega.direccion_entrega_router import direccion_entrega_router
from app.modules.categoria.categoria_router import categoria_router
from app.modules.ingrediente.ingrediente_router import ingrediente_router
from app.modules.producto.producto_router import producto_router
from app.modules.producto_categoria.producto_categoria_router import producto_categoria_router
from app.modules.producto_ingrediente.producto_ingrediente_router import producto_ingrediente_router
from app.modules.forma_pago.forma_pago_router import forma_pago_router
from app.modules.estado_pedido.estado_pedido_router import estado_pedido_router
from app.modules.pedido.pedido_router import pedido_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield
    print("aplicacion finalizada")

app = FastAPI(
    title="Segundo parcial",
    version="1.0.0",
    description=(
        "Proyecto para el parcial 2 de programacion 4\n\n" \
        "Gomez Cristian \n\n"
        "Guerra Martin"
    ),
    lifespan=lifespan,)
# CORS ---------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", 
                    "http://localhost:5174",],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers: Identidad & Acceso ─────────────────────────────────────────────
app.include_router(usuario_router)
app.include_router(usuario_rol_router)
app.include_router(rol_router)
app.include_router(direccion_entrega_router)

# Catalogo
app.include_router(categoria_router)
app.include_router(ingrediente_router)
app.include_router(producto_router)
app.include_router(producto_categoria_router)
app.include_router(producto_ingrediente_router)
app.include_router(forma_pago_router)
app.include_router(estado_pedido_router)

# Ventas
app.include_router(pedido_router)


# ─── Health check ─────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "version": "2.0.0"}
