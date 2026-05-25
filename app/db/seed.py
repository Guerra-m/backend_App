"""
Seed obligatorio — carga datos iniciales.
Idempotente: se puede ejecutar múltiples veces sin duplicar datos.

Uso:
    python -m app.db.seed

Crea:
  - Roles: ADMIN, STOCK, PEDIDOS, CLIENT
  - EstadoPedido: PENDIENTE, CONFIRMADO, EN_PREP, EN_CAMINO, ENTREGADO, CANCELADO
  - FormaPago: MERCADOPAGO, EFECTIVO, TRANSFERENCIA
  - Usuario admin por defecto
"""

from sqlmodel import Session, select
from app.core.database import engine, create_db_and_tables
from app.core.security import hash_password
from app.modules.rol.rol_model import Rol
from app.modules.usuario.usuario_model import Usuario
from app.modules.usuario_rol.usuario_rol_model import UsuarioRol
from app.modules.direccion_entrega.direccion_entrega_model import DireccionEntrega              # noqa: F401
from app.modules.refresh_token.refresh_token_model import RefreshToken                          # noqa: F401
from app.modules.forma_pago.forma_pago_model import FormaPago
from app.modules.estado_pedido.estado_pedido_model import EstadoPedido
from app.modules.categoria.categoria_model import Categoria                                    # noqa: F401
from app.modules.ingrediente.ingrediente_model import Ingrediente                              # noqa: F401
from app.modules.producto.producto_model import Producto                                       # noqa: F401
from app.modules.producto_categoria.producto_categoria_model import ProductoCategoria          # noqa: F401
from app.modules.producto_ingrediente.producto_ingrediente_model import ProductoIngrediente    # noqa: F401
from app.modules.pedido.pedido_model import Pedido                                              # noqa: F401
from app.modules.detalle_pedido.detalle_pedido_model import DetallePedido                       # noqa: F401
from app.modules.historial_estado_pedido.historial_estado_pedido_model import HistorialEstadoPedido  # noqa: F401
# Datos ------------

ROLES = [
    {"codigo": "ADMIN",   "nombre": "Administrador",     "descripcion": "Acceso total sin restricciones"},
    {"codigo": "STOCK",   "nombre": "Gestión de Stock",   "descripcion": "Actualiza stock y disponible"},
    {"codigo": "PEDIDOS", "nombre": "Gestión de Pedidos", "descripcion": "Avanza estados CONFIRMADO→ENTREGADO"},
    {"codigo": "CLIENT",  "nombre": "Cliente",            "descripcion": "Opera solo sus propios datos"},
]

ESTADO_PEDIDOS = [
    {"codigo": "PENDIENTE",  "descripcion": "Pedido recibido, en espera de confirmación", "orden": 1, "es_terminal": False},
    {"codigo": "CONFIRMADO", "descripcion": "Pedido confirmado, en preparación",           "orden": 2, "es_terminal": False},
    {"codigo": "EN_PREP",    "descripcion": "Pedido en proceso de preparación",            "orden": 3, "es_terminal": False},
    {"codigo": "EN_CAMINO",  "descripcion": "Pedido en tránsito para entrega",             "orden": 4, "es_terminal": False},
    {"codigo": "ENTREGADO",  "descripcion": "Pedido entregado al cliente",                 "orden": 5, "es_terminal": True},
    {"codigo": "CANCELADO",  "descripcion": "Pedido cancelado",                            "orden": 6, "es_terminal": True},
]

FORMA_PAGOS = [
    {"codigo": "MERCADOPAGO",   "descripcion": "Pago mediante Mercado Pago",          "habilitado": True},
    {"codigo": "EFECTIVO",      "descripcion": "Pago en efectivo al recibir el pedido", "habilitado": True},
    {"codigo": "TRANSFERENCIA", "descripcion": "Pago mediante transferencia bancaria", "habilitado": True},
]

USUARIOS = [
    {
        "nombre": "Admin",
        "apellido": "Sistema",
        "email": "admin@example.com",
        "password": "Admin1234!",
        "roles": ["ADMIN"],
    },
    {
        "nombre": "Juan",
        "apellido": "Pérez",
        "email": "juan@example.com",
        "password": "Juan1234!",
        "roles": ["CLIENT"],
    },
]


# Runner -----------

def run() -> None:
    print("=== Inyectando Seed — Parcial 2 Prog 4 ===\n")
    create_db_and_tables()

    with Session(engine) as session:
        print("Roles:")
        for data in ROLES:
            existing = session.get(Rol, data["codigo"])
            if existing:
                print(f"  [=] Ya existe: {data['codigo']}")
            else:
                session.add(Rol(**data))
                print(f"  [+] Creado: {data['codigo']}")
        session.commit()

        print("\nEstadoPedidos:")
        for data in ESTADO_PEDIDOS:
            existing = session.get(EstadoPedido, data["codigo"])
            if existing:
                print(f"  [=] Ya existe: {data['codigo']}")
            else:
                session.add(EstadoPedido(**data))
                print(f"  [+] Creado: {data['codigo']}")

        session.commit()

        print("\nFormas de Pago:")
        for data in FORMA_PAGOS:
            existing = session.get(FormaPago, data["codigo"])
            if existing:
                print(f"  [=] Ya existe: {data['codigo']}")
            else:
                session.add(FormaPago(**data))
                print(f"  [+] Creado: {data['codigo']}")

        session.commit()

        print("\nUsuarios:")
        for data in USUARIOS:
            existing = session.exec(
                select(Usuario).where(Usuario.email == data["email"])
            ).first()

            if existing:
                print(f"  [=] Ya existe: {data['email']}")
            else:
                usuario = Usuario(
                    nombre=data["nombre"],
                    apellido=data["apellido"],
                    email=data["email"],
                    password_hash=hash_password(data["password"]),
                )
                session.add(usuario)
                session.flush()

                for rol_codigo in data["roles"]:
                    session.add(UsuarioRol(
                        usuario_id=usuario.id,
                        rol_codigo=rol_codigo,
                    ))
                print(f"  [+] Creado: {data['email']} / {data['password']}  roles={data['roles']}")

        session.commit()

    print("\n--- Usuarios para pruebas ---")
    print("  admin@example.com / Admin1234!  → ADMIN")
    print("  juan@example.com  / Juan1234!   → CLIENT")
    


if __name__ == "__main__":
    run()