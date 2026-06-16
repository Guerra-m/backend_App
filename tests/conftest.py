"""
tests/conftest.py
=================
Fixtures compartidos por toda la suite de tests de FoodStore.
"""

import os

# Cargar .env.test ANTES de cualquier import de la app
from dotenv import load_dotenv
load_dotenv(".env.test", override=True)

# Forzar environment de test
os.environ["ENVIRONMENT"] = "test"
# Apuntar a SQLite en memoria
os.environ["TEST_DATABASE_URL"] = "sqlite://"
# Subir rate limit para no interferir con tests funcionales
os.environ["RATE_LIMIT_DEFAULT_PER_MINUTE"] = "10000"
os.environ["RATE_LIMIT_DEFAULT_BURST"] = "1000"
os.environ["RATE_LIMIT_AUTH_PER_MINUTE"] = "10000"
os.environ["RATE_LIMIT_AUTH_BURST"] = "1000"

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select
from sqlalchemy.pool import StaticPool

from app.core.database import get_session
from app.core.security import hash_password
from app.core.rate_limit.rate_limit_middleware import RateLimitMiddleware
from app.main import app

# Importar TODOS los modelos para que SQLModel.metadata los conozca
from app.modules.rol.rol_model import Rol
from app.modules.usuario.usuario_model import Usuario
from app.modules.usuario_rol.usuario_rol_model import UsuarioRol
from app.modules.refresh_token.refresh_token_model import RefreshToken
from app.modules.direccion_entrega.direccion_entrega_model import DireccionEntrega
from app.modules.unidad_medida.unidad_medida_model import UnidadMedida
from app.modules.categoria.categoria_model import Categoria
from app.modules.ingrediente.ingrediente_model import Ingrediente
from app.modules.producto.producto_model import Producto
from app.modules.producto_categoria.producto_categoria_model import ProductoCategoria
from app.modules.producto_ingrediente.producto_ingrediente_model import ProductoIngrediente
from app.modules.forma_pago.forma_pago_model import FormaPago
from app.modules.estado_pedido.estado_pedido_model import EstadoPedido
from app.modules.pedido.pedido_model import Pedido
from app.modules.detalle_pedido.detalle_pedido_model import DetallePedido
from app.modules.historial_estado_pedido.historial_estado_pedido_model import HistorialEstadoPedido
from app.modules.pago.pago_model import Pago


# ===========================================================================
# 1. ENGINE DE TEST
# ===========================================================================
@pytest.fixture(name="engine_test", scope="session")
def engine_test_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    yield engine
    engine.dispose()


# ===========================================================================
# 2. SESSION DE BD
# ===========================================================================
@pytest.fixture(name="session", scope="function")
def session_fixture(engine_test):
    SQLModel.metadata.create_all(engine_test)
    with Session(engine_test) as session:
        yield session
    SQLModel.metadata.drop_all(engine_test)


# ===========================================================================
# 3. CLIENTE HTTP
# ===========================================================================
@pytest.fixture(name="client", scope="function")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    _reset_rate_limiters()
    _seed_test_db(session)

    with TestClient(app, raise_server_exceptions=False) as client:
        yield client

    app.dependency_overrides.clear()


def _reset_rate_limiters() -> None:
    try:
        RateLimitMiddleware.reset_all_limiters()
    except Exception:
        pass


def _seed_test_db(session: Session) -> None:
    # Roles
    for codigo, nombre in [
        ("ADMIN", "Administrador"),
        ("STOCK", "Gestión de Stock"),
        ("PEDIDOS", "Gestión de Pedidos"),
        ("CLIENT", "Cliente"),
    ]:
        if not session.get(Rol, codigo):
            session.add(Rol(codigo=codigo, nombre=nombre, descripcion=nombre))

    # Estados de pedido
    estados = [
        ("PENDIENTE", "Pedido recibido", 1, False),
        ("CONFIRMADO", "Pago confirmado", 2, False),
        ("EN_PREP", "En preparacion", 3, False),
        ("ENTREGADO", "Entregado", 4, True),
        ("CANCELADO", "Cancelado", 5, True),
    ]
    for codigo, desc, orden, terminal in estados:
        if not session.get(EstadoPedido, codigo):
            session.add(EstadoPedido(
                codigo=codigo, descripcion=desc,
                orden=orden, es_terminal=terminal
            ))

    # Formas de pago
    for codigo, desc in [
        ("MERCADOPAGO", "MercadoPago"),
        ("EFECTIVO", "Efectivo"),
        ("TRANSFERENCIA", "Transferencia"),
    ]:
        if not session.get(FormaPago, codigo):
            session.add(FormaPago(codigo=codigo, descripcion=desc, habilitado=True))

    # Unidades de medida
    for nombre, simbolo, tipo in [
        ("unidad", "ud", "contable"),
        ("kilogramo", "kg", "peso"),
    ]:
        existing = session.exec(
            select(UnidadMedida).where(UnidadMedida.simbolo == simbolo)
        ).first()
        if not existing:
            session.add(UnidadMedida(nombre=nombre, simbolo=simbolo, tipo=tipo))

    session.flush()

    # Usuario admin
    admin_existing = session.exec(
        select(Usuario).where(Usuario.email == "admin@foodstore.com")
    ).first()
    if not admin_existing:
        admin = Usuario(
            nombre="Admin",
            apellido="Sistema",
            email="admin@foodstore.com",
            password_hash=hash_password("Admin1234!"),
        )
        session.add(admin)
        session.flush()
        session.add(UsuarioRol(usuario_id=admin.id, rol_codigo="ADMIN"))

    session.commit()


# ===========================================================================
# 4. FIXTURES DE DATOS
# ===========================================================================

@pytest.fixture(name="normal_user")
def normal_user_fixture(client: TestClient) -> dict:
    response = client.post("/api/v1/auth/register", json={
        "nombre": "Cliente",
        "apellido": "Test",
        "email": "cliente@test.com",
        "password": "Cliente1234!",
    })
    assert response.status_code == 201, f"Setup normal_user fallo: {response.json()}"
    return response.json()


@pytest.fixture(name="producto_payload")
def producto_payload_fixture() -> dict:
    return {
        "nombre": "Hamburguesa Test",
        "descripcion": "Producto de prueba",
        "precio_base": 1500.0,
        "stock_cantidad": 10,
        "disponible": True,
    }


@pytest.fixture(name="created_producto")
def created_producto_fixture(client: TestClient, admin_headers: dict, producto_payload: dict) -> dict:
    response = client.post(
        "/api/v1/productos/", json=producto_payload, headers=admin_headers
    )
    assert response.status_code == 201, f"Setup producto fallo: {response.json()}"
    return response.json()


@pytest.fixture(name="created_pedido")
def created_pedido_fixture(client: TestClient, user_headers: dict, created_producto: dict) -> dict:
    response = client.post(
        "/api/v1/pedidos/",
        json={
            "forma_pago_codigo": "EFECTIVO",
            "items": [
                {
                    "producto_id": created_producto["id"],
                    "cantidad": 1,
                    "personalizacion": [],
                }
            ],
        },
        headers=user_headers,
    )
    assert response.status_code == 201, f"Setup pedido fallo: {response.json()}"
    return response.json()


# ===========================================================================
# 5. HELPERS DE AUTENTICACION
# ===========================================================================

def _login(client: TestClient, email: str, password: str) -> dict:
    response = client.post(
        "/api/v1/auth/token",
        data={"username": email, "password": password},
    )
    if response.status_code != 200:
        raise RuntimeError(
            f"Login fallo para {email}: {response.status_code} {response.text}"
        )
    cookie = response.cookies.get("access_token")
    if not cookie:
        raise RuntimeError(f"Login OK pero sin cookie para {email}")
    return {"Cookie": f"access_token={cookie}"}


@pytest.fixture(name="admin_headers")
def admin_headers_fixture(client: TestClient) -> dict:
    return _login(client, "admin@foodstore.com", "Admin1234!")


@pytest.fixture(name="user_headers")
def user_headers_fixture(client: TestClient, normal_user: dict) -> dict:
    return _login(client, normal_user["email"], "Cliente1234!")