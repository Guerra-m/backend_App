from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class UsuarioCreate(BaseModel):
    """Datos requeridos para registrar un usuario."""
    nombre: str = Field(min_length=1, max_length=80)
    apellido: str = Field(min_length=1, max_length=80)
    email: EmailStr
    celular: Optional[str] = Field(default=None, max_length=20)
    password: str = Field(min_length=8)


class UsuarioUpdate(BaseModel):
    """Datos para actualizar perfil (parcial)."""
    nombre: Optional[str] = Field(default=None, max_length=80)
    apellido: Optional[str] = Field(default=None, max_length=80)
    celular: Optional[str] = Field(default=None, max_length=20)


class UsuarioRead(BaseModel):
    id: int
    nombre: str
    apellido: str
    email: str
    celular: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UsuarioReadWithRoles(UsuarioRead):
    roles: list[str] = []

    model_config = {"from_attributes": True}


class UsuarioAuth(BaseModel):
  
    id: int
    nombre: str
    apellido: str
    email: str
    celular: Optional[str]
    roles: list[str] = []


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # segundos hasta expiración


class TokenRefreshRequest(BaseModel):
    refresh_token: str
