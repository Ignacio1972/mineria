"""
Modelo SQLAlchemy para Documento.
"""
from datetime import datetime, date
from uuid import uuid4
from enum import Enum
from sqlalchemy import Column, String, Text, BigInteger, Integer, DateTime, Date, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID, ENUM, JSONB, ARRAY
from sqlalchemy.orm import relationship

from app.db.session import Base


class CategoriaDocumento(str, Enum):
    """Categorias de documentos (legacy)."""
    LEGAL = "legal"
    TECNICO = "tecnico"
    AMBIENTAL = "ambiental"
    CARTOGRAFIA = "cartografia"
    OTRO = "otro"


class CategoriaDocumentoSEA(str, Enum):
    """Categorías de documentos según requerimientos SEA."""
    # Documentos geográficos/cartográficos
    CARTOGRAFIA_PLANOS = "cartografia_planos"

    # Documentos de personal
    TITULO_PROFESIONAL = "titulo_profesional"
    CERTIFICADO_CONSULTORA = "certificado_consultora"
    CERTIFICADO_LABORATORIO = "certificado_laboratorio"

    # Estudios técnicos especializados
    ESTUDIO_AIRE = "estudio_aire"
    ESTUDIO_AGUA = "estudio_agua"
    ESTUDIO_SUELO = "estudio_suelo"
    ESTUDIO_FLORA = "estudio_flora"
    ESTUDIO_FAUNA = "estudio_fauna"
    ESTUDIO_SOCIAL = "estudio_social"
    ESTUDIO_ARQUEOLOGICO = "estudio_arqueologico"
    ESTUDIO_RUIDO = "estudio_ruido"
    ESTUDIO_VIBRACIONES = "estudio_vibraciones"
    ESTUDIO_PAISAJE = "estudio_paisaje"
    ESTUDIO_HIDROGEOLOGICO = "estudio_hidrogeologico"

    # Documentos legales y permisos
    RESOLUCION_SANITARIA = "resolucion_sanitaria"
    ANTECEDENTE_PAS = "antecedente_pas"
    CERTIFICADO_PERTENENCIA = "certificado_pertenencia"
    CONTRATO_SERVIDUMBRE = "contrato_servidumbre"

    # Participación ciudadana
    ACTA_PARTICIPACION = "acta_participacion"
    COMPROMISO_VOLUNTARIO = "compromiso_voluntario"
    CONSULTA_INDIGENA = "consulta_indigena"

    # Evaluaciones de riesgo
    EVALUACION_RIESGO = "evaluacion_riesgo"
    PLAN_EMERGENCIA = "plan_emergencia"
    PLAN_CIERRE = "plan_cierre"

    # Otros documentos técnicos
    MEMORIA_TECNICA = "memoria_tecnica"
    CRONOGRAMA = "cronograma"
    PRESUPUESTO_AMBIENTAL = "presupuesto_ambiental"
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

    # Categoría legacy (mantener compatibilidad)
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

    # Nueva categoría SEA específica
    categoria_sea = Column(
        ENUM(
            'cartografia_planos', 'titulo_profesional', 'certificado_consultora',
            'certificado_laboratorio', 'estudio_aire', 'estudio_agua', 'estudio_suelo',
            'estudio_flora', 'estudio_fauna', 'estudio_social', 'estudio_arqueologico',
            'estudio_ruido', 'estudio_vibraciones', 'estudio_paisaje', 'estudio_hidrogeologico',
            'resolucion_sanitaria', 'antecedente_pas', 'certificado_pertenencia',
            'contrato_servidumbre', 'acta_participacion', 'compromiso_voluntario',
            'consulta_indigena', 'evaluacion_riesgo', 'plan_emergencia', 'plan_cierre',
            'memoria_tecnica', 'cronograma', 'presupuesto_ambiental', 'otro',
            name="categoria_documento_sea",
            schema="proyectos",
            create_type=False
        ),
        nullable=True,
        default='otro',
        index=True
    )

    descripcion = Column(Text, nullable=True)
    archivo_path = Column(String(500), nullable=False)
    mime_type = Column(String(100), nullable=False)
    tamano_bytes = Column(BigInteger, nullable=False)
    checksum_sha256 = Column(String(64), nullable=True)

    # Nuevos campos para validación y metadatos
    validacion_formato = Column(JSONB, default={})  # {valido, errores, warnings, crs}
    contenido_extraido = Column(Text, nullable=True)  # Texto extraído del documento
    num_paginas = Column(Integer, nullable=True)
    profesional_responsable = Column(String(200), nullable=True)
    fecha_documento = Column(Date, nullable=True)
    fecha_vigencia = Column(Date, nullable=True)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relaciones
    proyecto = relationship("Proyecto", back_populates="documentos")

    def __repr__(self):
        return f"<DocumentoProyecto {self.nombre}>"

    @property
    def tamano_mb(self) -> float:
        """Retorna tamano en MB."""
        return round(self.tamano_bytes / (1024 * 1024), 2)

    @property
    def esta_vigente(self) -> bool:
        """Verifica si el documento está vigente."""
        if not self.fecha_vigencia:
            return True
        return self.fecha_vigencia >= date.today()


class RequerimientoDocumento(Base):
    """Requerimiento de documento por tipo de proyecto."""

    __tablename__ = "requerimientos_documentos"
    __table_args__ = {"schema": "asistente_config"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    tipo_proyecto_id = Column(
        ForeignKey("asistente_config.tipos_proyecto.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    subtipo_proyecto_id = Column(
        ForeignKey("asistente_config.subtipos_proyecto.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    categoria_sea = Column(
        ENUM(
            'cartografia_planos', 'titulo_profesional', 'certificado_consultora',
            'certificado_laboratorio', 'estudio_aire', 'estudio_agua', 'estudio_suelo',
            'estudio_flora', 'estudio_fauna', 'estudio_social', 'estudio_arqueologico',
            'estudio_ruido', 'estudio_vibraciones', 'estudio_paisaje', 'estudio_hidrogeologico',
            'resolucion_sanitaria', 'antecedente_pas', 'certificado_pertenencia',
            'contrato_servidumbre', 'acta_participacion', 'compromiso_voluntario',
            'consulta_indigena', 'evaluacion_riesgo', 'plan_emergencia', 'plan_cierre',
            'memoria_tecnica', 'cronograma', 'presupuesto_ambiental', 'otro',
            name="categoria_documento_sea",
            schema="proyectos",
            create_type=False
        ),
        nullable=False,
        index=True
    )

    # Obligatoriedad
    es_obligatorio = Column(Boolean, default=False)
    obligatorio_para_dia = Column(Boolean, default=False)
    obligatorio_para_eia = Column(Boolean, default=False)

    # Descripción
    nombre_display = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=True)
    notas_sea = Column(Text, nullable=True)

    # Validaciones
    formatos_permitidos = Column(ARRAY(Text), default=['application/pdf'])
    tamano_max_mb = Column(Integer, default=50)
    requiere_firma_digital = Column(Boolean, default=False)
    requiere_profesional_responsable = Column(Boolean, default=False)

    # Para cartografía
    requiere_crs_wgs84 = Column(Boolean, default=False)
    formatos_gis_permitidos = Column(ARRAY(Text), default=['shp', 'geojson', 'kml', 'gml'])

    # Presentación
    orden = Column(Integer, default=100)
    seccion_eia = Column(String(50), nullable=True)

    activo = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<RequerimientoDocumento {self.nombre_display}>"


class DocumentoValidacion(Base):
    """Estado de validación de documentos por proyecto."""

    __tablename__ = "documentos_validacion"
    __table_args__ = {"schema": "proyectos"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    proyecto_id = Column(
        ForeignKey("proyectos.proyectos.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    requerimiento_id = Column(
        ForeignKey("asistente_config.requerimientos_documentos.id", ondelete="SET NULL"),
        nullable=True
    )
    categoria_sea = Column(
        ENUM(
            'cartografia_planos', 'titulo_profesional', 'certificado_consultora',
            'certificado_laboratorio', 'estudio_aire', 'estudio_agua', 'estudio_suelo',
            'estudio_flora', 'estudio_fauna', 'estudio_social', 'estudio_arqueologico',
            'estudio_ruido', 'estudio_vibraciones', 'estudio_paisaje', 'estudio_hidrogeologico',
            'resolucion_sanitaria', 'antecedente_pas', 'certificado_pertenencia',
            'contrato_servidumbre', 'acta_participacion', 'compromiso_voluntario',
            'consulta_indigena', 'evaluacion_riesgo', 'plan_emergencia', 'plan_cierre',
            'memoria_tecnica', 'cronograma', 'presupuesto_ambiental', 'otro',
            name="categoria_documento_sea",
            schema="proyectos",
            create_type=False
        ),
        nullable=False,
        index=True
    )

    estado = Column(String(20), default='pendiente')  # pendiente, subido, validando, aprobado, rechazado, no_aplica
    documento_id = Column(
        ForeignKey("proyectos.documentos.id", ondelete="SET NULL"),
        nullable=True
    )

    validacion_formato = Column(Boolean, nullable=True)
    validacion_contenido = Column(Boolean, nullable=True)
    validacion_firma = Column(Boolean, nullable=True)

    observaciones = Column(Text, nullable=True)
    observaciones_sea = Column(Text, nullable=True)

    validado_por = Column(String(100), nullable=True)
    validado_fecha = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    documento = relationship("DocumentoProyecto", foreign_keys=[documento_id])

    def __repr__(self):
        return f"<DocumentoValidacion {self.categoria_sea} - {self.estado}>"
