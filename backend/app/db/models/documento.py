"""
Modelo SQLAlchemy para Documento.
"""
from datetime import datetime
from uuid import uuid4
from enum import Enum
from sqlalchemy import Column, String, Text, BigInteger, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import relationship

from app.db.session import Base


class CategoriaDocumento(str, Enum):
    """Categorias de documentos."""
    LEGAL = "legal"
    TECNICO = "tecnico"
    AMBIENTAL = "ambiental"
    CARTOGRAFIA = "cartografia"
    OTRO = "otro"


class DocumentoProyecto(Base):
    """Documento adjunto a un proyecto."""

    __tablename__ = "documentos"
    __table_args__ = {"schema": "proyectos"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    proyecto_id = Column(
        ForeignKey("proyectos.proyectos.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    nombre = Column(String(255), nullable=False)
    nombre_original = Column(String(255), nullable=False)
    categoria = Column(
        ENUM(
            'legal', 'tecnico', 'ambiental', 'cartografia', 'otro',
            name="categoria_documento",
            schema="proyectos",
            create_type=False
        ),
        nullable=False,
        default='otro',
        index=True
    )
    descripcion = Column(Text, nullable=True)
    archivo_path = Column(String(500), nullable=False)
    mime_type = Column(String(100), nullable=False)
    tamano_bytes = Column(BigInteger, nullable=False)
    checksum_sha256 = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relaciones
    proyecto = relationship("Proyecto", back_populates="documentos")

    def __repr__(self):
        return f"<DocumentoProyecto {self.nombre}>"

    @property
    def tamano_mb(self) -> float:
        """Retorna tamano en MB."""
        return round(self.tamano_bytes / (1024 * 1024), 2)
