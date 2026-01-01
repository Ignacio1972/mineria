"""
Schemas Pydantic para Documento.
"""
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field


class CategoriaDocumento(str, Enum):
    """Categorias de documentos."""
    LEGAL = "legal"
    TECNICO = "tecnico"
    AMBIENTAL = "ambiental"
    CARTOGRAFIA = "cartografia"
    OTRO = "otro"


class DocumentoBase(BaseModel):
    """Campos base del documento."""
    nombre: str = Field(..., min_length=1, max_length=255)
    categoria: CategoriaDocumento = CategoriaDocumento.OTRO
    descripcion: Optional[str] = None


class DocumentoCreate(DocumentoBase):
    """Schema para crear documento (el archivo se envia como form-data)."""
    pass


class DocumentoResponse(DocumentoBase):
    """Schema de respuesta del documento."""
    id: UUID
    proyecto_id: int
    nombre_original: str
    archivo_path: str
    mime_type: str
    tamano_bytes: int
    tamano_mb: float = 0.0
    checksum_sha256: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentoListResponse(BaseModel):
    """Lista de documentos."""
    items: List[DocumentoResponse]
    total: int
    total_bytes: int
    total_mb: float
