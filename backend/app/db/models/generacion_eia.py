"""
Modelos SQLAlchemy para Generación de EIA (Fase 4).
Esquemas: proyectos, asistente_config
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, BigInteger,
    ForeignKey, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db.session import Base


# =============================================================================
# ENUMS
# =============================================================================

class EstadoDocumento(str, Enum):
    """Estados posibles de un documento EIA."""
    BORRADOR = "borrador"
    EN_REVISION = "en_revision"
    VALIDADO = "validado"
    FINAL = "final"


class FormatoExportacion(str, Enum):
    """Formatos de exportación disponibles."""
    PDF = "pdf"
    DOCX = "docx"
    ESEIA_XML = "eseia_xml"


class TipoValidacion(str, Enum):
    """Tipos de validación SEA."""
    CONTENIDO = "contenido"
    FORMATO = "formato"
    REFERENCIA = "referencia"
    COMPLETITUD = "completitud"
    NORMATIVA = "normativa"


class Severidad(str, Enum):
    """Niveles de severidad de observaciones."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class EstadoObservacion(str, Enum):
    """Estados de observaciones de validación."""
    PENDIENTE = "pendiente"
    CORREGIDA = "corregida"
    IGNORADA = "ignorada"


# =============================================================================
# TABLA: proyectos.documentos_eia
# =============================================================================

class DocumentoEIA(Base):
    """Documento EIA generado con versionado."""

    __tablename__ = "documentos_eia"
    __table_args__ = {'schema': 'proyectos'}

    id = Column(Integer, primary_key=True, index=True)
    proyecto_id = Column(Integer, ForeignKey('proyectos.proyectos.id', ondelete='CASCADE'), nullable=False)
    version = Column(Integer, default=1)
    estado = Column(String(30), default=EstadoDocumento.BORRADOR.value, nullable=False)
    titulo = Column(String(500))
    contenido_capitulos = Column(JSONB)  # {1: {titulo, contenido, subsecciones}, ...}
    metadatos = Column(JSONB)  # {fecha, autores, empresa_consultora, etc}
    validaciones = Column(JSONB)  # Resultados de validación
    estadisticas = Column(JSONB)  # {paginas, palabras, figuras, tablas}
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    proyecto = relationship("Proyecto", back_populates="documentos_eia")
    versiones = relationship("VersionEIA", back_populates="documento", cascade="all, delete-orphan")
    exportaciones = relationship("ExportacionEIA", back_populates="documento", cascade="all, delete-orphan")
    observaciones = relationship("ObservacionValidacion", back_populates="documento", cascade="all, delete-orphan")


# =============================================================================
# TABLA: proyectos.versiones_eia
# =============================================================================

class VersionEIA(Base):
    """Historial de versiones de documentos EIA con snapshots."""

    __tablename__ = "versiones_eia"
    __table_args__ = (
        UniqueConstraint('documento_id', 'version', name='uq_documento_version'),
        {'schema': 'proyectos'}
    )

    id = Column(Integer, primary_key=True, index=True)
    documento_id = Column(Integer, ForeignKey('proyectos.documentos_eia.id', ondelete='CASCADE'), nullable=False)
    version = Column(Integer, nullable=False)
    cambios = Column(Text, nullable=False)
    contenido_snapshot = Column(JSONB)  # Snapshot completo del contenido
    creado_por = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    documento = relationship("DocumentoEIA", back_populates="versiones")


# =============================================================================
# TABLA: proyectos.exportaciones_eia
# =============================================================================

class ExportacionEIA(Base):
    """Registro de exportaciones de documentos EIA."""

    __tablename__ = "exportaciones_eia"
    __table_args__ = {'schema': 'proyectos'}

    id = Column(Integer, primary_key=True, index=True)
    documento_id = Column(Integer, ForeignKey('proyectos.documentos_eia.id', ondelete='CASCADE'), nullable=False)
    formato = Column(String(20), nullable=False)
    archivo_path = Column(String(500))
    tamano_bytes = Column(BigInteger)
    generado_exitoso = Column(Boolean, default=False)
    error_mensaje = Column(Text)
    configuracion = Column(JSONB)  # Config de exportación (estilos, márgenes, etc)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    documento = relationship("DocumentoEIA", back_populates="exportaciones")


# =============================================================================
# TABLA: asistente_config.reglas_validacion_sea
# =============================================================================

class ReglaValidacionSEA(Base):
    """Reglas de validación de documentos EIA según requisitos SEA/ICSARA."""

    __tablename__ = "reglas_validacion_sea"
    __table_args__ = {'schema': 'asistente_config'}

    id = Column(Integer, primary_key=True, index=True)
    tipo_proyecto_id = Column(Integer, ForeignKey('asistente_config.tipos_proyecto.id', ondelete='SET NULL'))
    capitulo_numero = Column(Integer)  # NULL = aplica a todo el documento
    codigo_regla = Column(String(50), unique=True, nullable=False)
    descripcion = Column(Text, nullable=False)
    tipo_validacion = Column(String(30), nullable=False)
    criterio = Column(JSONB, nullable=False)  # Regla estructurada
    mensaje_error = Column(Text, nullable=False)
    mensaje_sugerencia = Column(Text)
    severidad = Column(String(20), default=Severidad.WARNING.value)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    tipo_proyecto = relationship("TipoProyecto")
    observaciones = relationship("ObservacionValidacion", back_populates="regla")


# =============================================================================
# TABLA: asistente_config.templates_capitulos
# =============================================================================

class TemplateCapitulo(Base):
    """Templates de capítulos EIA por tipo de proyecto/industria."""

    __tablename__ = "templates_capitulos"
    __table_args__ = (
        UniqueConstraint('tipo_proyecto_id', 'capitulo_numero', name='uq_tipo_capitulo'),
        {'schema': 'asistente_config'}
    )

    id = Column(Integer, primary_key=True, index=True)
    tipo_proyecto_id = Column(Integer, ForeignKey('asistente_config.tipos_proyecto.id', ondelete='CASCADE'), nullable=False)
    capitulo_numero = Column(Integer, nullable=False)
    titulo = Column(String(200), nullable=False)
    template_prompt = Column(Text, nullable=False)  # Prompt para Claude
    estructura_esperada = Column(JSONB)  # Subsecciones esperadas
    instrucciones_generacion = Column(Text)
    ejemplos = Column(Text)  # Ejemplos del corpus SEA
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    tipo_proyecto = relationship("TipoProyecto")


# =============================================================================
# TABLA: proyectos.observaciones_validacion
# =============================================================================

class ObservacionValidacion(Base):
    """Observaciones detectadas durante validación de documentos EIA."""

    __tablename__ = "observaciones_validacion"
    __table_args__ = {'schema': 'proyectos'}

    id = Column(Integer, primary_key=True, index=True)
    documento_id = Column(Integer, ForeignKey('proyectos.documentos_eia.id', ondelete='CASCADE'), nullable=False)
    regla_id = Column(Integer, ForeignKey('asistente_config.reglas_validacion_sea.id', ondelete='SET NULL'))
    capitulo_numero = Column(Integer)
    seccion = Column(String(100))
    tipo_observacion = Column(String(30), nullable=False)
    severidad = Column(String(20), nullable=False)
    mensaje = Column(Text, nullable=False)
    sugerencia = Column(Text)
    contexto = Column(JSONB)  # Información adicional
    estado = Column(String(20), default=EstadoObservacion.PENDIENTE.value)
    created_at = Column(DateTime, default=datetime.utcnow)
    resuelta_at = Column(DateTime)

    # Relaciones
    documento = relationship("DocumentoEIA", back_populates="observaciones")
    regla = relationship("ReglaValidacionSEA", back_populates="observaciones")
