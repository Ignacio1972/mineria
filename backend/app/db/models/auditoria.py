"""
Modelo SQLAlchemy para Auditoria de Analisis.
"""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship

from app.db.session import Base


class AuditoriaAnalisis(Base):
    """Registro de auditoria para cumplimiento regulatorio SEIA."""

    __tablename__ = "auditoria_analisis"
    __table_args__ = {"schema": "proyectos"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    analisis_id = Column(
        ForeignKey("proyectos.analisis.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Trazabilidad GIS
    capas_gis_usadas = Column(JSONB, nullable=False, default=list)
    # Ejemplo: [{"nombre": "snaspe", "fecha": "2025-12-01", "version": "v2024.2"}]

    # Documentos referenciados
    documentos_referenciados = Column(ARRAY(UUID(as_uuid=True)), default=list)

    # Normativa citada
    normativa_citada = Column(JSONB, nullable=False, default=list)
    # Ejemplo: [{"tipo": "Ley", "numero": "19300", "articulo": "11", "letra": "d"}]

    # Integridad
    checksum_datos_entrada = Column(String(64), nullable=False)
    version_modelo_llm = Column(String(50), nullable=True)
    version_sistema = Column(String(20), nullable=True)

    # Metricas de ejecucion
    tiempo_gis_ms = Column(Integer, nullable=True)
    tiempo_rag_ms = Column(Integer, nullable=True)
    tiempo_llm_ms = Column(Integer, nullable=True)
    tokens_usados = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relaciones
    analisis = relationship("Analisis", back_populates="auditoria")

    def __repr__(self):
        return f"<AuditoriaAnalisis {self.id}>"
