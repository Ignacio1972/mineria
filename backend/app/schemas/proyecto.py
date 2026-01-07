"""
Schemas Pydantic para Proyecto.
"""
from uuid import UUID
from datetime import datetime
from typing import Optional, List, Any
from enum import Enum
from pydantic import BaseModel, Field


class EstadoProyecto(str, Enum):
    """Estados del proyecto."""
    BORRADOR = "borrador"
    COMPLETO = "completo"
    CON_GEOMETRIA = "con_geometria"
    ANALIZADO = "analizado"
    EN_REVISION = "en_revision"
    APROBADO = "aprobado"
    RECHAZADO = "rechazado"
    ARCHIVADO = "archivado"


class FaseProyecto(str, Enum):
    """Fases del workflow de generación EIA."""
    IDENTIFICACION = "identificacion"
    PREFACTIBILIDAD = "prefactibilidad"
    RECOPILACION = "recopilacion"
    GENERACION = "generacion"
    REFINAMIENTO = "refinamiento"


class MaterialRAG(BaseModel):
    """Material del corpus RAG asociado a un componente."""
    documento_id: int
    titulo: str
    contenido: str
    similitud: float = Field(..., ge=0, le=1)


class ComponenteChecklistBase(BaseModel):
    """Base para componente del checklist."""
    componente: str
    capitulo: int = Field(..., ge=1, le=11)
    nombre: str
    descripcion: Optional[str] = None
    requerido: bool = True
    prioridad: str = Field("media", pattern="^(alta|media|baja)$")
    estado: str = Field("pendiente", pattern="^(pendiente|en_progreso|completado)$")
    progreso_porcentaje: int = Field(0, ge=0, le=100)
    razon_inclusion: Optional[str] = None
    triggers_relacionados: List[str] = Field(default_factory=list)


class ComponenteChecklistCreate(ComponenteChecklistBase):
    """Schema para crear componente del checklist."""
    proyecto_id: int
    analisis_id: Optional[int] = None
    material_rag: List[MaterialRAG] = Field(default_factory=list)
    sugerencias_busqueda: List[str] = Field(default_factory=list)


class ComponenteChecklistResponse(ComponenteChecklistBase):
    """Schema de respuesta para componente del checklist."""
    id: int
    proyecto_id: int
    analisis_id: Optional[int] = None
    material_rag: List[MaterialRAG] = Field(default_factory=list)
    sugerencias_busqueda: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ComponenteChecklistUpdate(BaseModel):
    """Schema para actualizar componente del checklist."""
    estado: Optional[str] = Field(None, pattern="^(pendiente|en_progreso|completado)$")
    progreso_porcentaje: Optional[int] = Field(None, ge=0, le=100)


class GeometriaGeoJSON(BaseModel):
    """Geometria en formato GeoJSON."""
    type: str = Field(..., pattern="^(Polygon|MultiPolygon)$")
    coordinates: Any


class ProyectoBase(BaseModel):
    """Campos base del proyecto."""
    nombre: str = Field(..., min_length=2, max_length=200)
    cliente_id: Optional[UUID] = None
    tipo_mineria: Optional[str] = None
    mineral_principal: Optional[str] = None
    fase: Optional[str] = None
    titular: Optional[str] = None
    region: Optional[str] = None
    comuna: Optional[str] = None
    superficie_ha: Optional[float] = Field(None, ge=0)
    produccion_estimada: Optional[str] = None
    vida_util_anos: Optional[int] = Field(None, ge=0)
    uso_agua_lps: Optional[float] = Field(None, ge=0)
    fuente_agua: Optional[str] = None
    energia_mw: Optional[float] = Field(None, ge=0)
    trabajadores_construccion: Optional[int] = Field(None, ge=0)
    trabajadores_operacion: Optional[int] = Field(None, ge=0)
    inversion_musd: Optional[float] = Field(None, ge=0)
    descripcion: Optional[str] = None
    # Campos SEIA adicionales
    descarga_diaria_ton: Optional[float] = Field(None, ge=0)
    emisiones_co2_ton_ano: Optional[float] = Field(None, ge=0)
    requiere_reasentamiento: bool = False
    afecta_patrimonio: bool = False


class ProyectoCreate(ProyectoBase):
    """Schema para crear proyecto."""
    geometria: Optional[GeometriaGeoJSON] = None


class ProyectoUpdate(BaseModel):
    """Schema para actualizar proyecto (todos opcionales)."""
    nombre: Optional[str] = Field(None, min_length=2, max_length=200)
    cliente_id: Optional[UUID] = None
    tipo_mineria: Optional[str] = None
    mineral_principal: Optional[str] = None
    fase: Optional[str] = None
    titular: Optional[str] = None
    region: Optional[str] = None
    comuna: Optional[str] = None
    superficie_ha: Optional[float] = None
    produccion_estimada: Optional[str] = None
    vida_util_anos: Optional[int] = None
    uso_agua_lps: Optional[float] = None
    fuente_agua: Optional[str] = None
    energia_mw: Optional[float] = None
    trabajadores_construccion: Optional[int] = None
    trabajadores_operacion: Optional[int] = None
    inversion_musd: Optional[float] = None
    descripcion: Optional[str] = None
    descarga_diaria_ton: Optional[float] = None
    emisiones_co2_ton_ano: Optional[float] = None
    requiere_reasentamiento: Optional[bool] = None
    afecta_patrimonio: Optional[bool] = None


class ProyectoGeometriaUpdate(BaseModel):
    """Schema para actualizar solo geometria."""
    geometria: GeometriaGeoJSON


class CambioEstadoRequest(BaseModel):
    """Schema para cambiar estado del proyecto."""
    estado: EstadoProyecto
    motivo: Optional[str] = None


class CamposPreCalculados(BaseModel):
    """Campos GIS pre-calculados."""
    afecta_glaciares: bool = False
    dist_area_protegida_km: Optional[float] = None
    dist_comunidad_indigena_km: Optional[float] = None
    dist_centro_poblado_km: Optional[float] = None


class ProyectoResponse(ProyectoBase):
    """Schema de respuesta del proyecto."""
    id: int
    estado: str
    porcentaje_completado: int = 0
    # Workflow EIA
    fase_actual: str = "identificacion"
    progreso_global: int = 0
    # Estado del proyecto
    tiene_geometria: bool = False
    puede_analizar: bool = False
    # Campos pre-calculados
    afecta_glaciares: bool = False
    dist_area_protegida_km: Optional[float] = None
    dist_comunidad_indigena_km: Optional[float] = None
    dist_centro_poblado_km: Optional[float] = None
    # Descripción geográfica
    descripcion_geografica: Optional[str] = None
    descripcion_geografica_fecha: Optional[datetime] = None
    descripcion_geografica_fuente: Optional[str] = None
    # Info cliente
    cliente_razon_social: Optional[str] = None
    # Contadores
    total_documentos: int = 0
    total_analisis: int = 0
    ultimo_analisis: Optional[datetime] = None
    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProyectoConGeometriaResponse(ProyectoResponse):
    """Respuesta con geometria incluida."""
    geometria: Optional[GeometriaGeoJSON] = None


class ProyectoListResponse(BaseModel):
    """Lista paginada de proyectos."""
    items: List[ProyectoResponse]
    total: int
    page: int
    page_size: int
    pages: int


class FiltrosProyecto(BaseModel):
    """Filtros para listar proyectos."""
    cliente_id: Optional[UUID] = None
    estado: Optional[EstadoProyecto] = None
    region: Optional[str] = None
    busqueda: Optional[str] = None  # Busca en nombre
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
