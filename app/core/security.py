"""
Utilidades de seguridad centralizadas.
- Hashing de contraseña (bcrypt via passlib)
- Creación y verificación de JWT (HS256 viapython-jose)
- Hashing de refresh tokens (SHA256)
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# Hashing de contraseñas (bcrypt) ---------------

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

# JWT (Access Tokens) ------------------------------

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Genera un JWT firmado.
    Payload esperado: {"sub": str(usuario_id), "roles": ["ADMIN", ...]}
    """

    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
     )
    to_encode.update({"type": "access","exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_access_token(token: str) -> dict | None:
    """ Decodifica y valida un JWT, Retorna Payload o None """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None
    
# Refresh Token (SH256) ------------

def generate_refresh_token() -> str:
    """Genera un token aleatorio para refresh (64 chars hex)"""
    return secrets.token_hex(32)

def hash_refresh_token(token: str) -> str:
    """HS256 del refresh token para almacenar en BD"""
    return hashlib.sha256(token.encode()).hexdigest()
