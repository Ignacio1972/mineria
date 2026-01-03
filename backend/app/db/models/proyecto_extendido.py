"""
Modelos SQLAlchemy para tablas extendidas del proyecto.

Incluye: ubicaciones, características (ficha acumulativa), PAS,
análisis Art. 11, diagnósticos y conversaciones del asistente.

Esquema: proyectos.*
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Numeric,
    ForeignKey, UniqueConstraint, Index, Date, CheckConstraint
)
from sqlalchemy.dialects.postgresql import JSONB, UUID, ARRAY
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry

from app.db.session import Base


# =============================================================================
# ENUMS
# =============================================================================

class AlcanceTerritorial(str, Enum):
    """Alcance territorial del proyecto."""
    COMUNAL = "comunal"
    REGIONAL = "regional"
    BI_REGIONAL = "bi_regional"
    NACIONAL = "nacional"


class FuenteDato(str, Enum):
    """Origen del dato en la ficha."""
    MANUAL = "manual"
    ASISTENTE = "asistente"
    DOCUMENTO = "documento"
    GIS = "gis"


class EstadoPAS(str, Enum):
    """Estado de tramitación de un PAS."""
    IDENTIFICADO = "identificado"
    REQUERIDO = "requerido"
    NO_APLICA = "no_aplica"
    EN_TRAMITE = "en_tramite"
    APROBADO = "aprobado"
    RECHAZADO = "rechazado"


class EstadoAnalisisArt11(str, Enum):
    """Estado del análisis de cada literal del Art. 11."""
    PENDIENTE = "pendiente"
    NO_APLICA = "no_aplica"
    PROBABLE = "probable"
    CONFIRMADO = "confirmado"


class ViaSugerida(str, Enum):
    """Vía de ingreso sugerida."""
    DIA = "DIA"
    EIA = "EIA"
    NO_SEIA = "NO_SEIA"
    INDEFINIDO = "INDEFINIDO"


class EstadoConversacionProyecto(str, Enum):
    """Estado de la conversación del asistente por proyecto."""
    ACTIVA = "activa"
    PAUSADA = "pausada"
    COMPLETADA = "completada"
    ARCHIVADA = "archivada"


class FaseConversacion(str, Enum):
    """Fase del proceso de evaluación."""
    PREFACTIBILIDAD = "prefactibilidad"
    ESTRUCTURACION = "estructuracion"
    RECOPILACION = "recopilacion"
    GENERACION = "generacion"


class RolMensajeProyecto(str, Enum):
    """Rol del mensaje en conversación de proyecto."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


# =============================================================================
# MODELOS
# =============================================================================

class ProyectoUbicacion(Base):
    """
    Ubicaciones geográficas del proyecto con análisis GIS cacheado.
    Soporta versionamiento para historial de cambios.
    """

    __tablename__ = "proyecto_ubicaciones"
    __table_args__ = (
        Index('idx_ubicaciones_proyecto', 'proyecto_id'),
        Index('idx_ubicaciones_vigente', 'proyecto_id', 'es_vigente'),
        {"schema": "proyectos"}
    )

    id = Column(Integer, primary_key=True)
    proyecto_id = Column(
        Integer,
        ForeignKey("proyectos.proyectos.id", ondelete="CASCADE"),
        nullable=False
    )

    # Geometría
    geometria = Column(
        Geometry("GEOMETRY", srid=4326),
        nullable=False
    )

    # División político-administrativa
    regiones = Column(ARRAY(Text), nullable=True)
    provincias = Column(ARRAY(Text), nullable=True)
    comunas = Column(ARRAY(Text), nullable=True)

    # Alcance territorial
    alcance = Column(String(20), nullable=True)
    superficie_ha = Column(Numeric(12, 4), nullable=True)

    # Cache del análisis GIS
    analisis_gis_cache = Column(JSONB, default={})
    analisis_gis_fecha = Column(DateTime(timezone=True), nullable=True)

    # Versionamiento
    version = Column(Integer, default=1)
    es_vigente = Column(Boolean, default=True)

    # Origen del dato
    fuente = Column(String(50), default="manual")
    archivo_origen = Column(String(255), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    proyecto = relationship("Proyecto", backref="ubicaciones")

    def __repr__(self):
        return f"<ProyectoUbicacion {self.id} proyecto={self.proyecto_id} v{self.version}>"


class ProyectoCaracteristica(Base):
    """
    Ficha acumulativa estructurada del proyecto.
    Almacena características como pares clave-valor organizados por categoría.
    """

    __tablename__ = "proyecto_caracteristicas"
    __table_args__ = (
        UniqueConstraint('proyecto_id', 'categoria', 'clave', name='uq_caracteristica_proyecto_cat_clave'),
        Index('idx_caracteristicas_proyecto', 'proyecto_id'),
        Index('idx_caracteristicas_categoria', 'proyecto_id', 'categoria'),
        Index('idx_caracteristicas_clave', 'clave'),
        {"schema": "proyectos"}
    )

    id = Column(Integer, primary_key=True)
    proyecto_id = Column(
        Integer,
        ForeignKey("proyectos.proyectos.id", ondelete="CASCADE"),
        nullable=False
    )

    # Clasificación
    categoria = Column(String(50), nullable=False)  # 'identificacion', 'tecnico', 'obras', etc.
    clave = Column(String(100), nullable=False)

    # Valores
    valor = Column(Text, nullable=True)
    valor_numerico = Column(Numeric, nullable=True)
    unidad = Column(String(50), nullable=True)

    # Origen del dato
    fuente = Column(String(20), default="manual")
    documento_id = Column(
        UUID(as_uuid=True),
        ForeignKey("proyectos.documentos.id", ondelete="SET NULL"),
        nullable=True
    )
    pregunta_codigo = Column(String(50), nullable=True)

    # Validación
    validado = Column(Boolean, default=False)
    validado_por = Column(String(100), nullable=True)
    validado_fecha = Column(DateTime(timezone=True), nullable=True)

    # Metadatos
    notas = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    proyecto = relationship("Proyecto", backref="caracteristicas")

    def __repr__(self):
        return f"<ProyectoCaracteristica {self.categoria}.{self.clave}={self.valor}>"

    @property
    def valor_efectivo(self) -> Any:
        """Retorna el valor numérico si existe, sino el texto."""
        if self.valor_numerico is not None:
            return float(self.valor_numerico)
        return self.valor


class ProyectoPAS(Base):
    """
    Permisos Ambientales Sectoriales identificados para el proyecto.
    """

    __tablename__ = "proyecto_pas"
    __table_args__ = (
        UniqueConstraint('proyecto_id', 'articulo', name='uq_pas_proyecto_articulo'),
        Index('idx_pas_proyecto', 'proyecto_id'),
        Index('idx_pas_articulo', 'articulo'),
        Index('idx_pas_estado', 'estado'),
        {"schema": "proyectos"}
    )

    id = Column(Integer, primary_key=True)
    proyecto_id = Column(
        Integer,
        ForeignKey("proyectos.proyectos.id", ondelete="CASCADE"),
        nullable=False
    )

    # Identificación del PAS
    articulo = Column(Integer, nullable=False)
    nombre = Column(String(200), nullable=False)
    organismo = Column(String(100), nullable=False)

    # Estado
    estado = Column(String(30), default="identificado")
    obligatorio = Column(Boolean, default=False)

    # Justificación
    justificacion = Column(Text, nullable=True)
    condicion_activada = Column(JSONB, nullable=True)

    # Documentación
    documento_id = Column(
        UUID(as_uuid=True),
        ForeignKey("proyectos.documentos.id", ondelete="SET NULL"),
        nullable=True
    )
    numero_resolucion = Column(String(100), nullable=True)
    fecha_resolucion = Column(Date, nullable=True)

    # Metadatos
    identificado_por = Column(String(20), default="sistema")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    proyecto = relationship("Proyecto", backref="pas_identificados")

    def __repr__(self):
        return f"<ProyectoPAS Art.{self.articulo} estado={self.estado}>"


class ProyectoAnalisisArt11(Base):
    """
    Análisis de cada literal del Artículo 11 (DIA vs EIA).
    """

    __tablename__ = "proyecto_analisis_art11"
    __table_args__ = (
        UniqueConstraint('proyecto_id', 'literal', name='uq_art11_proyecto_literal'),
        Index('idx_art11_proyecto', 'proyecto_id'),
        Index('idx_art11_estado', 'estado'),
        {"schema": "proyectos"}
    )

    id = Column(Integer, primary_key=True)
    proyecto_id = Column(
        Integer,
        ForeignKey("proyectos.proyectos.id", ondelete="CASCADE"),
        nullable=False
    )

    # Literal analizado
    literal = Column(String(1), nullable=False)  # 'a', 'b', 'c', 'd', 'e', 'f'

    # Estado del análisis
    estado = Column(String(20), default="pendiente")

    # Justificación y evidencias
    justificacion = Column(Text, nullable=True)
    evidencias = Column(JSONB, default=[])

    # Origen del análisis
    fuente_gis = Column(Boolean, default=False)
    fuente_usuario = Column(Boolean, default=False)
    fuente_asistente = Column(Boolean, default=False)

    # Confianza
    confianza = Column(Integer, nullable=True)  # 0-100

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    proyecto = relationship("Proyecto", backref="analisis_art11")

    def __repr__(self):
        return f"<ProyectoAnalisisArt11 literal={self.literal} estado={self.estado}>"


class ProyectoDiagnostico(Base):
    """
    Resultados de diagnóstico de prefactibilidad.
    Permite múltiples versiones para historial.
    """

    __tablename__ = "proyecto_diagnosticos"
    __table_args__ = (
        Index('idx_diagnosticos_proyecto', 'proyecto_id'),
        Index('idx_diagnosticos_version', 'proyecto_id', 'version'),
        Index('idx_diagnosticos_via', 'via_sugerida'),
        {"schema": "proyectos"}
    )

    id = Column(Integer, primary_key=True)
    proyecto_id = Column(
        Integer,
        ForeignKey("proyectos.proyectos.id", ondelete="CASCADE"),
        nullable=False
    )

    # Versión
    version = Column(Integer, default=1)

    # Resultado principal
    via_sugerida = Column(String(10), nullable=True)  # 'DIA', 'EIA', 'NO_SEIA', 'INDEFINIDO'
    confianza = Column(Integer, nullable=True)  # 0-100

    # Detalles
    literales_gatillados = Column(ARRAY(String(1)), default=[])

    # Umbral SEIA
    cumple_umbral_seia = Column(Boolean, nullable=True)
    umbral_evaluado = Column(JSONB, nullable=True)

    # PAS y alertas
    permisos_identificados = Column(JSONB, default=[])
    alertas = Column(JSONB, default=[])
    recomendaciones = Column(JSONB, default=[])

    # Referencia a ubicación usada
    ubicacion_version_id = Column(
        Integer,
        ForeignKey("proyectos.proyecto_ubicaciones.id", ondelete="SET NULL"),
        nullable=True
    )

    # Resumen
    resumen = Column(Text, nullable=True)

    # Metadatos
    generado_por = Column(String(20), default="sistema")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relaciones
    proyecto = relationship("Proyecto", backref="diagnosticos")
    ubicacion = relationship("ProyectoUbicacion", backref="diagnosticos")

    def __repr__(self):
        return f"<ProyectoDiagnostico v{self.version} via={self.via_sugerida}>"


class ProyectoConversacion(Base):
    """
    Conversaciones del asistente específicas por proyecto.
    Diferente del chat general, sigue el flujo de evaluación EIA.
    """

    __tablename__ = "proyecto_conversaciones"
    __table_args__ = (
        Index('idx_proy_conv_proyecto', 'proyecto_id'),
        Index('idx_proy_conv_estado', 'estado'),
        Index('idx_proy_conv_fase', 'fase'),
        {"schema": "proyectos"}
    )

    id = Column(Integer, primary_key=True)
    proyecto_id = Column(
        Integer,
        ForeignKey("proyectos.proyectos.id", ondelete="CASCADE"),
        nullable=False
    )

    # Estado
    estado = Column(String(20), default="activa")
    fase = Column(String(50), default="prefactibilidad")

    # Progreso
    progreso_porcentaje = Column(Integer, default=0)
    ultima_pregunta_codigo = Column(String(50), nullable=True)

    # Resumen acumulativo
    resumen_actual = Column(Text, nullable=True)
    tokens_acumulados = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    proyecto = relationship("Proyecto", backref="conversaciones_asistente")
    mensajes = relationship(
        "ProyectoConversacionMensaje",
        back_populates="conversacion",
        cascade="all, delete-orphan",
        order_by="ProyectoConversacionMensaje.created_at"
    )

    def __repr__(self):
        return f"<ProyectoConversacion {self.id} fase={self.fase} progreso={self.progreso_porcentaje}%>"


class ProyectoConversacionMensaje(Base):
    """
    Mensajes individuales de las conversaciones de proyecto.
    """

    __tablename__ = "conversacion_mensajes"
    __table_args__ = (
        Index('idx_conv_msg_conversacion', 'conversacion_id'),
        Index('idx_conv_msg_created', 'conversacion_id', 'created_at'),
        {"schema": "proyectos"}
    )

    id = Column(Integer, primary_key=True)
    conversacion_id = Column(
        Integer,
        ForeignKey("proyectos.proyecto_conversaciones.id", ondelete="CASCADE"),
        nullable=False
    )

    # Contenido
    rol = Column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    contenido = Column(Text, nullable=False)

    # Documento adjunto
    documento_adjunto_id = Column(
        UUID(as_uuid=True),
        ForeignKey("proyectos.documentos.id", ondelete="SET NULL"),
        nullable=True
    )

    # Acciones ejecutadas
    acciones_ejecutadas = Column(JSONB, default=[])

    # Tracking
    tokens_usados = Column(Integer, default=0)
    modelo_usado = Column(String(50), nullable=True)

    # Timestamp
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relaciones
    conversacion = relationship("ProyectoConversacion", back_populates="mensajes")

    def __repr__(self):
        return f"<ProyectoConversacionMensaje {self.rol}: {self.contenido[:30]}...>"
