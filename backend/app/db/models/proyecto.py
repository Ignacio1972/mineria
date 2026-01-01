"""
Modelo SQLAlchemy para Proyecto y Analisis.
"""
from enum import Enum
from sqlalchemy import Column, Integer, String, Numeric, Text, Boolean, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry

from app.db.session import Base


class EstadoProyecto(str, Enum):
    """Estados del proyecto en workflow SEIA."""
    BORRADOR = "borrador"
    COMPLETO = "completo"
    CON_GEOMETRIA = "con_geometria"
    ANALIZADO = "analizado"
    EN_REVISION = "en_revision"
    APROBADO = "aprobado"
    RECHAZADO = "rechazado"
    ARCHIVADO = "archivado"


class Proyecto(Base):
    """Proyecto minero."""

    __tablename__ = "proyectos"
    __table_args__ = {"schema": "proyectos"}

    id = Column(Integer, primary_key=True)

    # Relacion con cliente
    cliente_id = Column(
        UUID(as_uuid=True),
        ForeignKey("proyectos.clientes.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Estado del proyecto
    estado = Column(String(20), default="borrador", index=True)
    porcentaje_completado = Column(Integer, default=0)

    # Datos basicos
    nombre = Column(String(255), nullable=False)
    tipo_mineria = Column(String(100))
    mineral_principal = Column(String(100))
    fase = Column(String(100))
    titular = Column(String(255))
    region = Column(String(100), index=True)
    comuna = Column(String(100))

    # Caracteristicas tecnicas
    superficie_ha = Column(Numeric(12, 2))
    produccion_estimada = Column(String(255))
    vida_util_anos = Column(Integer)

    # Recursos
    uso_agua_lps = Column(Numeric(10, 2))
    fuente_agua = Column(String(255))
    energia_mw = Column(Numeric(10, 2))

    # Empleo e inversion
    trabajadores_construccion = Column(Integer)
    trabajadores_operacion = Column(Integer)
    inversion_musd = Column(Numeric(12, 2))

    # Descripcion
    descripcion = Column(Text)

    # Campos SEIA adicionales
    descarga_diaria_ton = Column(Numeric(12, 2), nullable=True)
    emisiones_co2_ton_ano = Column(Numeric(12, 2), nullable=True)
    requiere_reasentamiento = Column(Boolean, default=False)
    afecta_patrimonio = Column(Boolean, default=False)

    # Campos pre-calculados GIS (actualizados por trigger)
    afecta_glaciares = Column(Boolean, default=False)
    dist_area_protegida_km = Column(Numeric(8, 2), nullable=True)
    dist_comunidad_indigena_km = Column(Numeric(8, 2), nullable=True)
    dist_centro_poblado_km = Column(Numeric(8, 2), nullable=True)

    # Metadatos (renombrado a datos_extra porque 'metadata' es reservado en SQLAlchemy)
    datos_extra = Column("metadata", JSONB)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Geometria (AHORA OPCIONAL)
    geom = Column(
        Geometry("MULTIPOLYGON", srid=4326),
        nullable=True
    )

    # Relaciones
    cliente = relationship("Cliente", back_populates="proyectos")
    analisis = relationship(
        "Analisis",
        back_populates="proyecto",
        lazy="dynamic",
        cascade="all, delete-orphan"
    )
    documentos = relationship(
        "DocumentoProyecto",
        back_populates="proyecto",
        lazy="dynamic",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Proyecto {self.nombre}>"

    @property
    def tiene_geometria(self) -> bool:
        return self.geom is not None

    @property
    def puede_analizar(self) -> bool:
        """Verifica si el proyecto puede ser analizado."""
        return self.tiene_geometria and self.estado not in ['archivado']


class Analisis(Base):
    """Analisis de prefactibilidad ambiental."""

    __tablename__ = "analisis"
    __table_args__ = {"schema": "proyectos"}

    id = Column(Integer, primary_key=True)
    proyecto_id = Column(Integer, ForeignKey("proyectos.proyectos.id", ondelete="CASCADE"))
    fecha_analisis = Column(DateTime, default=func.now())

    # Tipo de analisis
    tipo_analisis = Column(String(20), default="completo")

    # Resultados GIS
    resultado_gis = Column(JSONB)

    # Clasificacion SEIA
    via_ingreso_recomendada = Column(String(50))
    confianza_clasificacion = Column(Numeric(3, 2))
    triggers_eia = Column(JSONB)

    # Normativa aplicable
    normativa_relevante = Column(JSONB)

    # Informe generado
    informe_texto = Column(Text)
    informe_json = Column(JSONB)

    # Metadata
    version_modelo = Column(String(50))
    tiempo_procesamiento_ms = Column(Integer)
    datos_extra = Column("metadata", JSONB)

    # Relaciones
    proyecto = relationship("Proyecto", back_populates="analisis")
    auditoria = relationship(
        "AuditoriaAnalisis",
        back_populates="analisis",
        uselist=False,
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Analisis {self.id} - {self.via_ingreso_recomendada}>"


class HistorialEstado(Base):
    """Historial de cambios de estado de proyectos."""

    __tablename__ = "historial_estados"
    __table_args__ = {"schema": "proyectos"}

    id = Column(UUID(as_uuid=True), primary_key=True)
    proyecto_id = Column(Integer, ForeignKey("proyectos.proyectos.id", ondelete="CASCADE"))
    estado_anterior = Column(String(20))
    estado_nuevo = Column(String(20), nullable=False)
    motivo = Column(Text)
    created_at = Column(DateTime, default=func.now())
