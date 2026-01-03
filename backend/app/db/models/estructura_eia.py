"""
Modelos SQLAlchemy para Estructura EIA (Fase 2).
Esquemas: asistente_config, proyectos
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime,
    ForeignKey, UniqueConstraint, Enum as SQLEnum
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import relationship

from app.db.session import Base


# =============================================================================
# ENUMS
# =============================================================================

class EstadoCapitulo(str, Enum):
    """Estados posibles de un capítulo del EIA."""
    PENDIENTE = "pendiente"
    EN_PROGRESO = "en_progreso"
    COMPLETADO = "completado"


class EstadoPAS(str, Enum):
    """Estados de tramitación de un PAS."""
    IDENTIFICADO = "identificado"
    REQUERIDO = "requerido"
    EN_TRAMITE = "en_tramite"
    APROBADO = "aprobado"
    NO_APLICA = "no_aplica"


class EstadoAnexo(str, Enum):
    """Estados de elaboración de un anexo."""
    PENDIENTE = "pendiente"
    EN_ELABORACION = "en_elaboracion"
    COMPLETADO = "completado"


class NivelComplejidad(str, Enum):
    """Niveles de complejidad del EIA."""
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"
    MUY_ALTA = "muy_alta"


class InstrumentoAmbiental(str, Enum):
    """Tipos de instrumento ambiental."""
    EIA = "EIA"
    DIA = "DIA"


# =============================================================================
# MODELOS DE CONFIGURACIÓN (asistente_config)
# =============================================================================

class CapituloEIA(Base):
    """Capítulos del EIA según Art. 18 DS 40, adaptados por tipo de proyecto."""

    __tablename__ = "capitulos_eia"
    __table_args__ = (
        UniqueConstraint('tipo_proyecto_id', 'numero', name='capitulos_eia_tipo_proyecto_id_numero_key'),
        {"schema": "asistente_config"}
    )

    id = Column(Integer, primary_key=True)
    tipo_proyecto_id = Column(
        Integer,
        ForeignKey("asistente_config.tipos_proyecto.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    numero = Column(Integer, nullable=False)
    titulo = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=True)
    contenido_requerido = Column(JSONB, default=list)
    es_obligatorio = Column(Boolean, default=True)
    orden = Column(Integer, nullable=False)
    activo = Column(Boolean, default=True)
    aplica_instrumento = Column(
        ARRAY(String),
        default=['EIA'],
        comment="Instrumentos a los que aplica: EIA, DIA o ambos"
    )
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relaciones
    tipo_proyecto = relationship("TipoProyecto")
    componentes_linea_base = relationship(
        "ComponenteLineaBase",
        back_populates="capitulo",
        foreign_keys="ComponenteLineaBase.capitulo_numero",
        primaryjoin="CapituloEIA.numero == foreign(ComponenteLineaBase.capitulo_numero)"
    )

    def __repr__(self):
        return f"<CapituloEIA {self.numero}: {self.titulo}>"

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el capítulo a diccionario."""
        return {
            "id": self.id,
            "numero": self.numero,
            "titulo": self.titulo,
            "descripcion": self.descripcion,
            "contenido_requerido": self.contenido_requerido or [],
            "es_obligatorio": self.es_obligatorio,
            "orden": self.orden,
            "aplica_instrumento": self.aplica_instrumento or ['EIA']
        }

    def aplica_a(self, instrumento: str) -> bool:
        """Verifica si el capítulo aplica a un instrumento específico."""
        return instrumento in (self.aplica_instrumento or ['EIA'])


class ComponenteLineaBase(Base):
    """Componentes ambientales a caracterizar en línea de base."""

    __tablename__ = "componentes_linea_base"
    __table_args__ = (
        UniqueConstraint('tipo_proyecto_id', 'codigo', name='componentes_linea_base_tipo_proyecto_id_codigo_key'),
        {"schema": "asistente_config"}
    )

    id = Column(Integer, primary_key=True)
    tipo_proyecto_id = Column(
        Integer,
        ForeignKey("asistente_config.tipos_proyecto.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    subtipo_id = Column(
        Integer,
        ForeignKey("asistente_config.subtipos_proyecto.id", ondelete="SET NULL"),
        nullable=True
    )
    capitulo_numero = Column(Integer, default=3, index=True)
    codigo = Column(String(50), nullable=False)
    nombre = Column(String(150), nullable=False)
    descripcion = Column(Text, nullable=True)
    metodologia = Column(Text, nullable=True)
    variables_monitorear = Column(JSONB, default=list)
    estudios_requeridos = Column(JSONB, default=list)
    duracion_estimada_dias = Column(Integer, default=30)
    es_obligatorio = Column(Boolean, default=True)
    condicion_activacion = Column(JSONB, nullable=True)
    orden = Column(Integer, default=0)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relaciones
    tipo_proyecto = relationship("TipoProyecto")
    subtipo = relationship("SubtipoProyecto")
    capitulo = relationship(
        "CapituloEIA",
        foreign_keys=[capitulo_numero],
        primaryjoin="ComponenteLineaBase.capitulo_numero == CapituloEIA.numero",
        viewonly=True
    )

    def __repr__(self):
        return f"<ComponenteLineaBase {self.codigo}: {self.nombre}>"

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el componente a diccionario."""
        return {
            "id": self.id,
            "codigo": self.codigo,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "metodologia": self.metodologia,
            "variables_monitorear": self.variables_monitorear or [],
            "estudios_requeridos": self.estudios_requeridos or [],
            "duracion_estimada_dias": self.duracion_estimada_dias,
            "es_obligatorio": self.es_obligatorio,
            "orden": self.orden
        }

    def aplica(self, caracteristicas: dict) -> bool:
        """Evalúa si el componente aplica según características del proyecto."""
        if self.es_obligatorio and not self.condicion_activacion:
            return True

        if not self.condicion_activacion:
            return False

        for campo, valor_esperado in self.condicion_activacion.items():
            if caracteristicas.get(campo) != valor_esperado:
                return False
        return True


# =============================================================================
# MODELO DE CONFIGURACIÓN POR INSTRUMENTO
# =============================================================================

class EstructuraPorInstrumento(Base):
    """Configuración de estructura según instrumento ambiental (EIA vs DIA)."""

    __tablename__ = "estructura_por_instrumento"
    __table_args__ = (
        UniqueConstraint('instrumento', 'tipo_proyecto_id', name='estructura_por_instrumento_instrumento_tipo_key'),
        {"schema": "asistente_config"}
    )

    id = Column(Integer, primary_key=True)
    instrumento = Column(String(3), nullable=False)  # 'EIA' o 'DIA'
    tipo_proyecto_id = Column(
        Integer,
        ForeignKey("asistente_config.tipos_proyecto.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )

    # Configuración de estructura
    capitulos_requeridos = Column(ARRAY(Integer), nullable=False)
    max_paginas_resumen = Column(Integer, nullable=False)
    requiere_linea_base = Column(Boolean, default=True)
    requiere_prediccion_impactos = Column(Boolean, default=True)
    requiere_plan_mitigacion = Column(Boolean, default=True)
    requiere_plan_contingencias = Column(Boolean, default=True)
    requiere_plan_seguimiento = Column(Boolean, default=True)

    # Plazos legales
    plazo_evaluacion_dias = Column(Integer, nullable=False)
    plazo_prorroga_dias = Column(Integer, nullable=False)
    max_icsara = Column(Integer, default=2)

    # Metadatos
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relaciones
    tipo_proyecto = relationship("TipoProyecto")

    def __repr__(self):
        return f"<EstructuraPorInstrumento {self.instrumento} tipo={self.tipo_proyecto_id}>"

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            "id": self.id,
            "instrumento": self.instrumento,
            "tipo_proyecto_id": self.tipo_proyecto_id,
            "capitulos_requeridos": self.capitulos_requeridos or [],
            "max_paginas_resumen": self.max_paginas_resumen,
            "requiere_linea_base": self.requiere_linea_base,
            "requiere_prediccion_impactos": self.requiere_prediccion_impactos,
            "requiere_plan_mitigacion": self.requiere_plan_mitigacion,
            "requiere_plan_contingencias": self.requiere_plan_contingencias,
            "requiere_plan_seguimiento": self.requiere_plan_seguimiento,
            "plazo_evaluacion_dias": self.plazo_evaluacion_dias,
            "plazo_prorroga_dias": self.plazo_prorroga_dias,
            "max_icsara": self.max_icsara
        }


# =============================================================================
# MODELO DE INSTANCIA POR PROYECTO (proyectos)
# =============================================================================

class EstructuraEIAProyecto(Base):
    """Estructura EIA/DIA generada para cada proyecto."""

    __tablename__ = "estructura_eia"
    __table_args__ = (
        UniqueConstraint('proyecto_id', 'version', name='estructura_eia_proyecto_id_version_key'),
        {"schema": "proyectos"}
    )

    id = Column(Integer, primary_key=True)
    proyecto_id = Column(
        Integer,
        ForeignKey("proyectos.proyectos.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    version = Column(Integer, default=1)
    instrumento = Column(
        String(3),
        default='EIA',
        comment="Tipo de instrumento: EIA o DIA"
    )
    capitulos = Column(JSONB, nullable=False, default=list)
    pas_requeridos = Column(JSONB, nullable=False, default=list)
    anexos_requeridos = Column(JSONB, nullable=False, default=list)
    plan_linea_base = Column(JSONB, default=list)
    estimacion_complejidad = Column(JSONB, nullable=True)
    notas = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(PGUUID(as_uuid=True), nullable=True)

    # Relaciones
    proyecto = relationship("Proyecto", backref="estructuras_eia")

    def __repr__(self):
        return f"<EstructuraEIAProyecto proyecto_id={self.proyecto_id} v{self.version}>"

    @property
    def progreso_general(self) -> int:
        """Calcula el progreso general de la estructura."""
        if not self.capitulos:
            return 0
        completados = sum(1 for c in self.capitulos if c.get("estado") == "completado")
        return round((completados / len(self.capitulos)) * 100)

    @property
    def capitulos_completados(self) -> int:
        """Cuenta capítulos completados."""
        if not self.capitulos:
            return 0
        return sum(1 for c in self.capitulos if c.get("estado") == "completado")

    @property
    def pas_aprobados(self) -> int:
        """Cuenta PAS aprobados."""
        if not self.pas_requeridos:
            return 0
        return sum(1 for p in self.pas_requeridos if p.get("estado") == "aprobado")

    def actualizar_capitulo(self, numero: int, estado: str, progreso: int = None) -> bool:
        """Actualiza el estado de un capítulo."""
        for cap in self.capitulos:
            if cap.get("numero") == numero:
                cap["estado"] = estado
                if progreso is not None:
                    cap["progreso_porcentaje"] = progreso
                return True
        return False

    def actualizar_pas(self, articulo: int, estado: str) -> bool:
        """Actualiza el estado de un PAS."""
        for pas in self.pas_requeridos:
            if pas.get("articulo") == articulo:
                pas["estado"] = estado
                return True
        return False

    def actualizar_anexo(self, codigo: str, estado: str) -> bool:
        """Actualiza el estado de un anexo."""
        for anexo in self.anexos_requeridos:
            if anexo.get("codigo") == codigo:
                anexo["estado"] = estado
                return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la estructura a diccionario completo."""
        return {
            "id": self.id,
            "proyecto_id": self.proyecto_id,
            "version": self.version,
            "instrumento": self.instrumento or "EIA",
            "capitulos": self.capitulos or [],
            "pas_requeridos": self.pas_requeridos or [],
            "anexos_requeridos": self.anexos_requeridos or [],
            "plan_linea_base": self.plan_linea_base or [],
            "estimacion_complejidad": self.estimacion_complejidad,
            "progreso_general": self.progreso_general,
            "capitulos_completados": self.capitulos_completados,
            "pas_aprobados": self.pas_aprobados,
            "notas": self.notas,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
