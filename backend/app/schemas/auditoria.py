"""
Schemas Pydantic para Auditoria de Analisis.
"""
from uuid import UUID
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field


class NormativaCitada(BaseModel):
    """Normativa citada en el analisis."""
    tipo: str = Field(..., description="Tipo de norma (Ley, DS, Reglamento)")
    numero: str = Field(..., description="Numero de la norma")
    articulo: Optional[str] = Field(None, description="Articulo especifico")
    letra: Optional[str] = Field(None, description="Letra del articulo (a-f)")
    descripcion: Optional[str] = Field(None, description="Descripcion breve")


class CapaGISUsada(BaseModel):
    """Capa GIS utilizada en el analisis."""
    nombre: str = Field(..., description="Nombre de la capa")
    fecha: str = Field(..., description="Fecha de la capa")
    version: Optional[str] = Field(None, description="Version de la capa")
    elementos_encontrados: int = Field(0, description="Elementos encontrados")


class MetricasEjecucion(BaseModel):
    """Metricas de ejecucion del analisis."""
    tiempo_gis_ms: int = Field(..., description="Tiempo de analisis GIS en ms")
    tiempo_rag_ms: int = Field(0, description="Tiempo de busqueda RAG en ms")
    tiempo_llm_ms: int = Field(0, description="Tiempo de generacion LLM en ms")
    tiempo_total_ms: int = Field(..., description="Tiempo total en ms")
    tokens_usados: int = Field(0, description="Tokens consumidos por LLM")


class AuditoriaAnalisisCreate(BaseModel):
    """Schema para crear registro de auditoria."""
    analisis_id: int
    capas_gis_usadas: List[CapaGISUsada]
    documentos_referenciados: List[UUID] = []
    normativa_citada: List[NormativaCitada]
    checksum_datos_entrada: str
    version_modelo_llm: Optional[str] = None
    version_sistema: str = "1.0.0"
    tiempo_gis_ms: Optional[int] = None
    tiempo_rag_ms: Optional[int] = None
    tiempo_llm_ms: Optional[int] = None
    tokens_usados: Optional[int] = None


class AuditoriaAnalisisResponse(BaseModel):
    """Schema de respuesta de auditoria."""
    id: UUID
    analisis_id: int
    capas_gis_usadas: List[CapaGISUsada]
    documentos_referenciados: List[UUID]
    normativa_citada: List[NormativaCitada]
    checksum_datos_entrada: str
    version_modelo_llm: Optional[str]
    version_sistema: Optional[str]
    tiempo_gis_ms: Optional[int]
    tiempo_rag_ms: Optional[int]
    tiempo_llm_ms: Optional[int]
    tokens_usados: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class AnalisisIntegradoInput(BaseModel):
    """Input para analisis integrado."""
    proyecto_id: int = Field(..., description="ID del proyecto a analizar")
    tipo: str = Field(
        "completo",
        description="Tipo de analisis: 'rapido' (sin LLM) o 'completo' (con LLM)",
        pattern="^(rapido|completo)$"
    )
    secciones: Optional[List[str]] = Field(
        None,
        description="Secciones especificas a generar (solo para tipo 'completo')"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "proyecto_id": 1,
                "tipo": "completo",
                "secciones": None
            }
        }


class AnalisisIntegradoResponse(BaseModel):
    """Respuesta del analisis integrado."""
    analisis_id: int = Field(..., description="ID del analisis creado")
    auditoria_id: UUID = Field(..., description="ID del registro de auditoria")
    proyecto_id: int
    fecha_analisis: datetime
    tipo_analisis: str

    # Clasificacion
    via_ingreso_recomendada: str
    confianza: float
    nivel_confianza: str
    justificacion: str

    # Resultados
    triggers_detectados: int
    alertas_criticas: int
    alertas_altas: int
    alertas_totales: int

    # Estado actualizado
    estado_proyecto: str

    # Metricas
    metricas: MetricasEjecucion

    # Informe (solo si tipo=completo)
    informe: Optional[dict] = None

    class Config:
        from_attributes = True
