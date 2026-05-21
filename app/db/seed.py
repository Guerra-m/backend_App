from sqlmodel import Session, select
from app.core.database import engine, create_db_and_tables
from app.core.security import hash_password
from app.modules.rol.rol_model import Rol
from app.modules.usuario.usuario_model import Usuario
from app.modules.usuario_rol.usuario_rol_model import UsuarioRol
from app.modules.direccion_entrega.direccion_entrega_model import DireccionEntrega  # noqa: F401
from app.modules.refresh_token.refresh_token_model import RefreshToken 


ROLES = [
    {"codigo": "ADMIN",   "nombre": "Administrador",     "descripcion": "Acceso total sin restricciones"},
    {"codigo": "STOCK",   "nombre": "Gestión de Stock",   "descripcion": "Actualiza stock y disponible"},
    {"codigo": "PEDIDOS", "nombre": "Gestión de Pedidos", "descripcion": "Avanza estados CONFIRMADO→ENTREGADO"},
    {"codigo": "CLIENT",  "nombre": "Cliente",            "descripcion": "Opera solo sus propios datos"},
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