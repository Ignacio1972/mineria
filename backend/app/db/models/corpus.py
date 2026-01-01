"""
Modelos SQLAlchemy para el Sistema de Gestion Documental RAG.

Este modulo define las entidades para:
- Categorias (taxonomia jerarquica)
- Archivos originales (PDFs/DOCX)
- Temas (clasificacion de fragmentos)
- Colecciones (agrupaciones tematicas)
- Relaciones entre documentos
- Plazos del proceso SEIA
- Actores del SEIA
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Float, DateTime,
    ForeignKey, ARRAY, CheckConstraint, UniqueConstraint, BigInteger
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.db.session import Base


class Categoria(Base):
    """
    Taxonomia jerarquica de documentos del corpus RAG.
    Implementa un arbol con auto-referencia.
    """
    __tablename__ = "categorias"
    __table_args__ = (
        CheckConstraint("nivel >= 1 AND nivel <= 5", name="nivel_valido"),
        {"schema": "legal"}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Jerarquia
    parent_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("legal.categorias.id", ondelete="CASCADE"), nullable=True
    )
    nivel: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    orden: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Identificacion
    codigo: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Configuracion
    tipo_documentos_permitidos: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String(100)), default=list
    )
    icono: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)

    # Estado
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relaciones
    parent = relationship("Categoria", remote_side=[id], back_populates="hijos")
    hijos = relationship("Categoria", back_populates="parent", cascade="all, delete-orphan")
    documentos = relationship("Documento", back_populates="categoria")

    def __repr__(self):
        return f"<Categoria(id={self.id}, codigo='{self.codigo}', nombre='{self.nombre}')>"


class ArchivoOriginal(Base):
    """
    Almacena referencias a archivos fisicos (PDF/DOCX) con hash de integridad.
    """
    __tablename__ = "archivos_originales"
    __table_args__ = (
        UniqueConstraint("hash_sha256", name="archivo_hash_unico"),
        {"schema": "legal"}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Archivo fisico
    nombre_original: Mapped[str] = mapped_column(String(500), nullable=False)
    nombre_storage: Mapped[str] = mapped_column(String(255), nullable=False)
    ruta_storage: Mapped[str] = mapped_column(String(1000), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    tamano_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # Integridad
    hash_sha256: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)

    # Procesamiento
    texto_extraido: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    paginas: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    procesado_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Auditoria
    subido_por: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relaciones
    documento = relationship("Documento", back_populates="archivo", uselist=False)

    def __repr__(self):
        return f"<ArchivoOriginal(id={self.id}, nombre='{self.nombre_original}')>"


class Tema(Base):
    """
    Catalogo de temas para clasificacion consistente de fragmentos.
    """
    __tablename__ = "temas"
    __table_args__ = {"schema": "legal"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Agrupacion
    grupo: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Keywords para deteccion automatica
    keywords: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text), default=list)

    # UI
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    icono: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relaciones
    fragmentos = relationship(
        "Fragmento",
        secondary="legal.fragmentos_temas",
        back_populates="temas_rel"
    )

    def __repr__(self):
        return f"<Tema(id={self.id}, codigo='{self.codigo}', nombre='{self.nombre}')>"


class Coleccion(Base):
    """
    Agrupaciones tematicas transversales de documentos.
    """
    __tablename__ = "colecciones"
    __table_args__ = {"schema": "legal"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Configuracion
    es_publica: Mapped[bool] = mapped_column(Boolean, default=True)
    orden: Mapped[int] = mapped_column(Integer, default=0)

    # UI
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    icono: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Auditoria
    creado_por: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relaciones
    documentos = relationship(
        "Documento",
        secondary="legal.documentos_colecciones",
        back_populates="colecciones"
    )

    def __repr__(self):
        return f"<Coleccion(id={self.id}, codigo='{self.codigo}', nombre='{self.nombre}')>"


class FragmentoTema(Base):
    """
    Tabla junction para relacion many-to-many entre fragmentos y temas.
    """
    __tablename__ = "fragmentos_temas"
    __table_args__ = {"schema": "legal"}

    fragmento_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("legal.fragmentos.id", ondelete="CASCADE"), primary_key=True
    )
    tema_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("legal.temas.id", ondelete="CASCADE"), primary_key=True
    )

    # Metadatos de la relacion
    confianza: Mapped[float] = mapped_column(Float, default=1.0)
    detectado_por: Mapped[str] = mapped_column(String(20), default="manual")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class DocumentoColeccion(Base):
    """
    Tabla junction para relacion many-to-many entre documentos y colecciones.
    """
    __tablename__ = "documentos_colecciones"
    __table_args__ = {"schema": "legal"}

    documento_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("legal.documentos.id", ondelete="CASCADE"), primary_key=True
    )
    coleccion_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("legal.colecciones.id", ondelete="CASCADE"), primary_key=True
    )

    orden: Mapped[int] = mapped_column(Integer, default=0)
    notas: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    agregado_por: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class RelacionDocumento(Base):
    """
    Relaciones entre documentos (reglamenta, interpreta, reemplaza, etc.).
    """
    __tablename__ = "relaciones_documentos"
    __table_args__ = (
        UniqueConstraint(
            "documento_origen_id", "documento_destino_id", "tipo_relacion",
            name="relacion_unica"
        ),
        CheckConstraint(
            "documento_origen_id != documento_destino_id",
            name="no_auto_relacion"
        ),
        {"schema": "legal"}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    documento_origen_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("legal.documentos.id", ondelete="CASCADE"), nullable=False
    )
    documento_destino_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("legal.documentos.id", ondelete="CASCADE"), nullable=False
    )

    # Tipos: reglamenta, interpreta, reemplaza, complementa, cita, modifica
    tipo_relacion: Mapped[str] = mapped_column(String(50), nullable=False)

    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relaciones
    documento_origen = relationship(
        "Documento",
        foreign_keys=[documento_origen_id],
        back_populates="relaciones_salientes"
    )
    documento_destino = relationship(
        "Documento",
        foreign_keys=[documento_destino_id],
        back_populates="relaciones_entrantes"
    )


class HistorialVersion(Base):
    """
    Auditoria de cambios en documentos.
    """
    __tablename__ = "historial_versiones"
    __table_args__ = {"schema": "legal"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    documento_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("legal.documentos.id", ondelete="CASCADE"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)

    # Snapshot del documento
    datos_documento: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Cambio
    tipo_cambio: Mapped[str] = mapped_column(String(50), nullable=False)
    descripcion_cambio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Auditoria
    realizado_por: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relaciones
    documento = relationship("Documento", back_populates="historial")


class PlazoProceso(Base):
    """
    Plazos legales del proceso SEIA para DIA y EIA.
    Basado en los diagramas oficiales del SEA.
    """
    __tablename__ = "plazos_proceso"
    __table_args__ = {"schema": "legal"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    instrumento: Mapped[str] = mapped_column(String(10), nullable=False)  # DIA o EIA
    etapa: Mapped[str] = mapped_column(String(100), nullable=False)
    plazo_dias: Mapped[int] = mapped_column(Integer, nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    normativa_referencia: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    orden: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<PlazoProceso(instrumento='{self.instrumento}', etapa='{self.etapa}', dias={self.plazo_dias})>"


class ActorSeia(Base):
    """
    Actores del Sistema de Evaluacion de Impacto Ambiental.
    """
    __tablename__ = "actores_seia"
    __table_args__ = {"schema": "legal"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sigla: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    nombre_completo: Mapped[str] = mapped_column(String(255), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rol: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    url_sitio: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)

    def __repr__(self):
        return f"<ActorSeia(sigla='{self.sigla}', nombre='{self.nombre_completo}')>"
