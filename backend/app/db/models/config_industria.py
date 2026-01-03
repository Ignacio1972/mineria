"""
Modelos SQLAlchemy para configuración por industria del asistente.
Esquema: asistente_config
"""
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Numeric,
    ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.orm import relationship

from app.db.session import Base


# =============================================================================
# ENUMS
# =============================================================================

class Obligatoriedad(str, Enum):
    """Niveles de obligatoriedad de un PAS."""
    OBLIGATORIO = "obligatorio"
    FRECUENTE = "frecuente"
    CASO_A_CASO = "caso_a_caso"


class TipoNorma(str, Enum):
    """Tipos de normativa ambiental."""
    CALIDAD = "calidad"
    EMISION = "emision"
    SECTORIAL = "sectorial"
    GENERAL = "general"


class RelevanciaOAECA(str, Enum):
    """Relevancia del OAECA para un tipo de proyecto."""
    PRINCIPAL = "principal"
    SECUNDARIO = "secundario"


class FaseProyecto(str, Enum):
    """Fases del proyecto donde aplica un impacto."""
    CONSTRUCCION = "construccion"
    OPERACION = "operacion"
    CIERRE = "cierre"
    TODAS = "todas"


class FrecuenciaImpacto(str, Enum):
    """Frecuencia de ocurrencia de un impacto."""
    MUY_COMUN = "muy_comun"
    FRECUENTE = "frecuente"
    OCASIONAL = "ocasional"


class TipoRespuesta(str, Enum):
    """Tipos de respuesta para preguntas del árbol."""
    TEXTO = "texto"
    NUMERO = "numero"
    OPCION = "opcion"
    ARCHIVO = "archivo"
    UBICACION = "ubicacion"
    BOOLEAN = "boolean"
    FECHA = "fecha"


class ResultadoUmbral(str, Enum):
    """Resultado de la evaluación de umbral SEIA."""
    INGRESA_SEIA = "ingresa_seia"
    NO_INGRESA = "no_ingresa"
    REQUIERE_EIA = "requiere_eia"


# =============================================================================
# MODELOS
# =============================================================================

class TipoProyecto(Base):
    """Tipos de proyecto según Art. 3 DS 40 (industrias)."""

    __tablename__ = "tipos_proyecto"
    __table_args__ = {"schema": "asistente_config"}

    id = Column(Integer, primary_key=True)
    codigo = Column(String(50), unique=True, nullable=False, index=True)
    nombre = Column(String(100), nullable=False)
    letra_art3 = Column(String(5), nullable=True)
    descripcion = Column(Text, nullable=True)
    activo = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relaciones
    subtipos = relationship(
        "SubtipoProyecto",
        back_populates="tipo_proyecto",
        cascade="all, delete-orphan"
    )
    umbrales = relationship(
        "UmbralSEIA",
        back_populates="tipo_proyecto",
        cascade="all, delete-orphan"
    )
    pas = relationship(
        "PASPorTipo",
        back_populates="tipo_proyecto",
        cascade="all, delete-orphan"
    )
    normativas = relationship(
        "NormativaPorTipo",
        back_populates="tipo_proyecto",
        cascade="all, delete-orphan"
    )
    oaecas = relationship(
        "OAECAPorTipo",
        back_populates="tipo_proyecto",
        cascade="all, delete-orphan"
    )
    impactos = relationship(
        "ImpactoPorTipo",
        back_populates="tipo_proyecto",
        cascade="all, delete-orphan"
    )
    anexos = relationship(
        "AnexoPorTipo",
        back_populates="tipo_proyecto",
        cascade="all, delete-orphan"
    )
    preguntas = relationship(
        "ArbolPregunta",
        back_populates="tipo_proyecto",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<TipoProyecto {self.codigo}: {self.nombre}>"


class SubtipoProyecto(Base):
    """Subtipos específicos de cada industria."""

    __tablename__ = "subtipos_proyecto"
    __table_args__ = (
        UniqueConstraint('tipo_proyecto_id', 'codigo', name='uq_subtipo_tipo_codigo'),
        {"schema": "asistente_config"}
    )

    id = Column(Integer, primary_key=True)
    tipo_proyecto_id = Column(
        Integer,
        ForeignKey("asistente_config.tipos_proyecto.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    codigo = Column(String(50), nullable=False)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text, nullable=True)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relaciones
    tipo_proyecto = relationship("TipoProyecto", back_populates="subtipos")
    umbrales = relationship("UmbralSEIA", back_populates="subtipo")
    pas = relationship("PASPorTipo", back_populates="subtipo")
    impactos = relationship("ImpactoPorTipo", back_populates="subtipo")
    anexos = relationship("AnexoPorTipo", back_populates="subtipo")
    preguntas = relationship("ArbolPregunta", back_populates="subtipo")

    def __repr__(self):
        return f"<SubtipoProyecto {self.codigo}: {self.nombre}>"


class UmbralSEIA(Base):
    """Umbrales para determinar ingreso al SEIA según DS 40."""

    __tablename__ = "umbrales_seia"
    __table_args__ = {"schema": "asistente_config"}

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
        nullable=True,
        index=True
    )
    parametro = Column(String(100), nullable=False)
    operador = Column(String(10), nullable=False)
    valor = Column(Numeric, nullable=False)
    unidad = Column(String(50), nullable=True)
    resultado = Column(String(50), nullable=False)
    descripcion = Column(Text, nullable=True)
    norma_referencia = Column(String(100), nullable=True)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relaciones
    tipo_proyecto = relationship("TipoProyecto", back_populates="umbrales")
    subtipo = relationship("SubtipoProyecto", back_populates="umbrales")

    def __repr__(self):
        return f"<UmbralSEIA {self.parametro} {self.operador} {self.valor}>"

    def evaluar(self, valor_proyecto: float) -> bool:
        """Evalúa si un valor cumple el umbral."""
        umbral = float(self.valor)
        if self.operador == ">=":
            return valor_proyecto >= umbral
        elif self.operador == ">":
            return valor_proyecto > umbral
        elif self.operador == "<=":
            return valor_proyecto <= umbral
        elif self.operador == "<":
            return valor_proyecto < umbral
        elif self.operador == "=":
            return valor_proyecto == umbral
        return False


class PASPorTipo(Base):
    """PAS típicos por tipo de proyecto."""

    __tablename__ = "pas_por_tipo"
    __table_args__ = {"schema": "asistente_config"}

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
    articulo = Column(Integer, nullable=False)
    nombre = Column(String(200), nullable=False)
    organismo = Column(String(100), nullable=False)
    obligatoriedad = Column(String(20), nullable=False)
    condicion_activacion = Column(JSONB, nullable=True)
    descripcion = Column(Text, nullable=True)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relaciones
    tipo_proyecto = relationship("TipoProyecto", back_populates="pas")
    subtipo = relationship("SubtipoProyecto", back_populates="pas")

    def __repr__(self):
        return f"<PASPorTipo Art.{self.articulo}: {self.nombre}>"

    def aplica(self, caracteristicas: dict) -> bool:
        """Evalúa si el PAS aplica según las características del proyecto."""
        if not self.condicion_activacion:
            return self.obligatoriedad == "obligatorio"

        for campo, valor_esperado in self.condicion_activacion.items():
            if caracteristicas.get(campo) != valor_esperado:
                return False
        return True


class NormativaPorTipo(Base):
    """Normativa ambiental aplicable por industria."""

    __tablename__ = "normativa_por_tipo"
    __table_args__ = {"schema": "asistente_config"}

    id = Column(Integer, primary_key=True)
    tipo_proyecto_id = Column(
        Integer,
        ForeignKey("asistente_config.tipos_proyecto.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    norma = Column(String(100), nullable=False)
    nombre = Column(String(200), nullable=False)
    componente = Column(String(100), nullable=True)
    tipo_norma = Column(String(50), nullable=True)
    aplica_siempre = Column(Boolean, default=False)
    descripcion = Column(Text, nullable=True)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relaciones
    tipo_proyecto = relationship("TipoProyecto", back_populates="normativas")

    def __repr__(self):
        return f"<NormativaPorTipo {self.norma}: {self.nombre}>"


class OAECAPorTipo(Base):
    """OAECA relevantes por tipo de proyecto."""

    __tablename__ = "oaeca_por_tipo"
    __table_args__ = {"schema": "asistente_config"}

    id = Column(Integer, primary_key=True)
    tipo_proyecto_id = Column(
        Integer,
        ForeignKey("asistente_config.tipos_proyecto.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    organismo = Column(String(100), nullable=False)
    competencias = Column(ARRAY(String(100)), nullable=True)
    relevancia = Column(String(20), nullable=False)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relaciones
    tipo_proyecto = relationship("TipoProyecto", back_populates="oaecas")

    def __repr__(self):
        return f"<OAECAPorTipo {self.organismo} ({self.relevancia})>"


class ImpactoPorTipo(Base):
    """Impactos típicos por tipo de proyecto."""

    __tablename__ = "impactos_por_tipo"
    __table_args__ = {"schema": "asistente_config"}

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
    componente = Column(String(100), nullable=False)
    impacto = Column(Text, nullable=False)
    fase = Column(String(50), nullable=True)
    frecuencia = Column(String(20), nullable=True)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relaciones
    tipo_proyecto = relationship("TipoProyecto", back_populates="impactos")
    subtipo = relationship("SubtipoProyecto", back_populates="impactos")

    def __repr__(self):
        return f"<ImpactoPorTipo {self.componente}: {self.impacto[:50]}...>"


class AnexoPorTipo(Base):
    """Anexos técnicos requeridos por tipo de proyecto."""

    __tablename__ = "anexos_por_tipo"
    __table_args__ = {"schema": "asistente_config"}

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
    codigo = Column(String(10), nullable=False)
    nombre = Column(String(200), nullable=False)
    profesional_responsable = Column(String(100), nullable=True)
    obligatorio = Column(Boolean, default=False)
    condicion_activacion = Column(JSONB, nullable=True)
    descripcion = Column(Text, nullable=True)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relaciones
    tipo_proyecto = relationship("TipoProyecto", back_populates="anexos")
    subtipo = relationship("SubtipoProyecto", back_populates="anexos")

    def __repr__(self):
        return f"<AnexoPorTipo {self.codigo}: {self.nombre}>"

    def aplica(self, caracteristicas: dict) -> bool:
        """Evalúa si el anexo aplica según las características del proyecto."""
        if self.obligatorio and not self.condicion_activacion:
            return True

        if not self.condicion_activacion:
            return False

        for campo, valor_esperado in self.condicion_activacion.items():
            if caracteristicas.get(campo) != valor_esperado:
                return False
        return True


class ArbolPregunta(Base):
    """Preguntas configurables por tipo/subtipo de proyecto."""

    __tablename__ = "arboles_preguntas"
    __table_args__ = (
        UniqueConstraint('tipo_proyecto_id', 'codigo', name='uq_arbol_tipo_codigo'),
        Index('idx_arboles_orden', 'tipo_proyecto_id', 'orden'),
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
    codigo = Column(String(50), nullable=False)
    pregunta_texto = Column(Text, nullable=False)
    tipo_respuesta = Column(String(20), nullable=False)
    opciones = Column(JSONB, nullable=True)
    orden = Column(Integer, default=0)
    es_obligatoria = Column(Boolean, default=False)
    campo_destino = Column(String(100), nullable=True)
    categoria_destino = Column(String(50), nullable=True)
    condicion_activacion = Column(JSONB, nullable=True)
    valida_umbral = Column(Boolean, default=False)
    ayuda = Column(Text, nullable=True)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relaciones
    tipo_proyecto = relationship("TipoProyecto", back_populates="preguntas")
    subtipo = relationship("SubtipoProyecto", back_populates="preguntas")

    def __repr__(self):
        return f"<ArbolPregunta {self.codigo}: {self.pregunta_texto[:50]}...>"

    def debe_mostrarse(self, respuestas_previas: dict) -> bool:
        """Evalúa si la pregunta debe mostrarse según respuestas previas."""
        if not self.condicion_activacion:
            return True

        condicion = self.condicion_activacion
        if "campo" in condicion and "valor" in condicion:
            campo = condicion["campo"]
            valor_esperado = condicion["valor"]
            return respuestas_previas.get(campo) == valor_esperado

        return True
