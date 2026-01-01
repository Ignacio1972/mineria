"""
Schemas Pydantic para Cliente.
"""
import re
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, field_validator


class ClienteBase(BaseModel):
    """Campos base del cliente."""
    rut: Optional[str] = Field(None, max_length=12, description="RUT chileno (ej: 12.345.678-9)")
    razon_social: str = Field(..., min_length=2, max_length=200)
    nombre_fantasia: Optional[str] = Field(None, max_length=200)
    email: Optional[EmailStr] = None
    telefono: Optional[str] = Field(None, max_length=20)
    direccion: Optional[str] = None
    notas: Optional[str] = None

    @field_validator('rut')
    @classmethod
    def validar_rut(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == '':
            return None
        # Validar formato basico: XX.XXX.XXX-X o XXXXXXXX-X
        clean = v.replace('.', '').replace('-', '')
        if not (7 <= len(clean) <= 9):
            raise ValueError('RUT invalido: longitud incorrecta')
        # Verificar que termine con digito o K
        if not re.match(r'^\d+[0-9kK]$', clean):
            raise ValueError('RUT invalido: formato incorrecto')
        return v.upper()


class ClienteCreate(ClienteBase):
    """Schema para crear cliente."""
    pass


class ClienteUpdate(BaseModel):
    """Schema para actualizar cliente (todos opcionales)."""
    rut: Optional[str] = Field(None, max_length=12)
    razon_social: Optional[str] = Field(None, min_length=2, max_length=200)
    nombre_fantasia: Optional[str] = None
    email: Optional[EmailStr] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    notas: Optional[str] = None
    activo: Optional[bool] = None

    @field_validator('rut')
    @classmethod
    def validar_rut(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == '':
            return None
        clean = v.replace('.', '').replace('-', '')
        if not (7 <= len(clean) <= 9):
            raise ValueError('RUT invalido: longitud incorrecta')
        if not re.match(r'^\d+[0-9kK]$', clean):
            raise ValueError('RUT invalido: formato incorrecto')
        return v.upper()


class ClienteResponse(ClienteBase):
    """Schema de respuesta del cliente."""
    id: UUID
    activo: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    cantidad_proyectos: int = 0

    class Config:
        from_attributes = True


class ClienteListResponse(BaseModel):
    """Lista paginada de clientes."""
    items: List[ClienteResponse]
    total: int
    page: int
    page_size: int
    pages: int
