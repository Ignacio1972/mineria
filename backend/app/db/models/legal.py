"""
Modelos SQLAlchemy para documentos legales y fragmentos del corpus RAG.
"""

from datetime import date, datetime
from typing import List, Optional
from sqlalchemy import (
    Column, Integer, String, Text, Date, DateTime, ForeignKey, ARRAY
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from pgvector.sqlalchemy import Vector

from app.db.session import Base
from app.core.config import settings


class Documento(Base):
    """
    Documento legal del corpus RAG (Ley, Reglamento, Guia SEA, etc.).
    """
    __tablename__ = "documentos"
    __table_args__ = {"schema": "legal"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Identificacion basica
    titulo: Mapped[str] = mapped_column(String(500), nullable=False)
    tipo: Mapped[str] = mapped_column(String(100), nullable=False)
    numero: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Fechas
    fecha_publicacion: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    fecha_vigencia: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    fecha_vigencia_fin: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Fuente
    organismo: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    url_fuente: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    resolucion_aprobatoria: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Contenido
    contenido_completo: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resumen: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Estado
    estado: Mapped[str] = mapped_column(String(50), default="vigente")

    # Clasificacion - Categoria
    categoria_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("legal.categorias.id"), nullable=True
    )

    # Archivo original
    archivo_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("legal.archivos_originales.id"), nullable=True
    )

    # Versionado
    version: Mapped[int] = mapped_column(Integer, default=1)
    version_anterior_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("legal.documentos.id"), nullable=True
    )

    # Aplicabilidad - Arrays
    sectores: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String(100)), default=list
    )
    tipologias_art3: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String(20)), default=list
    )
    triggers_art11: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String(1)), default=list
    )
    componentes_ambientales: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String(50)), default=list
    )
    regiones_aplicables: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String(50)), default=list
    )
    palabras_clave: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String(100)), default=list
    )

    # Proceso SEIA
    etapa_proceso: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    actor_principal: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Metadata adicional (JSONB para flexibilidad)
    datos_extra = Column("metadata", JSONB, nullable=True)

    # Auditoria
    creado_por: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    modificado_por: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relaciones
    fragmentos = relationship("Fragmento", back_populates="documento", cascade="all, delete-orphan")
    categoria = relationship("Categoria", back_populates="documentos")
    archivo = relationship("ArchivoOriginal", back_populates="documento")
    version_anterior = relationship("Documento", remote_side=[id], foreign_keys=[version_anterior_id])
    historial = relationship("HistorialVersion", back_populates="documento", cascade="all, delete-orphan")

    # Relaciones con colecciones
    colecciones = relationship(
        "Coleccion",
        secondary="legal.documentos_colecciones",
        back_populates="documentos"
    )

    # Relaciones entre documentos
    relaciones_salientes = relationship(
        "RelacionDocumento",
        foreign_keys="RelacionDocumento.documento_origen_id",
        back_populates="documento_origen",
        cascade="all, delete-orphan"
    )
    relaciones_entrantes = relationship(
        "RelacionDocumento",
        foreign_keys="RelacionDocumento.documento_destino_id",
        back_populates="documento_destino",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Documento(id={self.id}, tipo='{self.tipo}', titulo='{self.titulo[:50]}...')>"

    @property
    def tiene_archivo(self) -> bool:
        """Indica si el documento tiene archivo original asociado."""
        return self.archivo_id is not None

    @property
    def fragmentos_count(self) -> int:
        """Cantidad de fragmentos del documento."""
        return len(self.fragmentos) if self.fragmentos else 0


class Fragmento(Base):
    """
    Fragmento de un documento legal para busqueda vectorial RAG.
    """
    __tablename__ = "fragmentos"
    __table_args__ = {"schema": "legal"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    documento_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("legal.documentos.id", ondelete="CASCADE"), nullable=False
    )

    # Ubicacion en el documento
    seccion: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    numero_seccion: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Contenido
    contenido: Mapped[str] = mapped_column(Text, nullable=False)

    # Temas (array legacy, mantener compatibilidad)
    temas: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String(255)), default=list)

    # Embedding vectorial
    embedding = Column(Vector(settings.EMBEDDING_DIMENSION), nullable=True)

    # Metadata adicional
    datos_extra = Column("metadata", JSONB, nullable=True)

    # Auditoria
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relaciones
    documento = relationship("Documento", back_populates="fragmentos")

    # Relacion con temas (nueva, many-to-many)
    temas_rel = relationship(
        "Tema",
        secondary="legal.fragmentos_temas",
        back_populates="fragmentos"
    )

    def __repr__(self):
        return f"<Fragmento(id={self.id}, documento_id={self.documento_id}, seccion='{self.seccion}')>"

    @property
    def tiene_embedding(self) -> bool:
        """Indica si el fragmento tiene embedding generado."""
        return self.embedding is not None
