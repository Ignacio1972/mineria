"""
Schemas Pydantic para Estructura EIA (Fase 2).
Define tipos para capítulos, PAS, anexos, línea base y estimación de complejidad.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


# =============================================================================
# Enums
# =============================================================================

class EstadoCapituloEnum(str, Enum):
    """Estados posibles de un capítulo del EIA."""
    PENDIENTE = "pendiente"
    EN_PROGRESO = "en_progreso"
    COMPLETADO = "completado"


class EstadoPASEnum(str, Enum):
    """Estados de tramitación de un PAS."""
    IDENTIFICADO = "identificado"
    REQUERIDO = "requerido"
    EN_TRAMITE = "en_tramite"
    APROBADO = "aprobado"
    NO_APLICA = "no_aplica"


class EstadoAnexoEnum(str, Enum):
    """Estados de elaboración de un anexo."""
    PENDIENTE = "pendiente"
    EN_ELABORACION = "en_elaboracion"
    COMPLETADO = "completado"


class NivelComplejidadEnum(str, Enum):
    """Niveles de complejidad del EIA."""
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"
    MUY_ALTA = "muy_alta"


class ObligatoriedadPASEnum(str, Enum):
    """Obligatoriedad de un PAS."""
    OBLIGATORIO = "obligatorio"
    FRECUENTE = "frecuente"
    CASO_A_CASO = "caso_a_caso"


class InstrumentoAmbientalEnum(str, Enum):
    """Tipo de instrumento ambiental."""
    EIA = "EIA"
    DIA = "DIA"


# =============================================================================
# Capítulos EIA (Configuración)
# =============================================================================

class CapituloEIABase(BaseModel):
    """Base para capítulo del EIA."""
    numero: int = Field(..., ge=1, le=11, description="Número del capítulo (1-11)")
    titulo: str = Field(..., min_length=5, max_length=200)
    descripcion: Optional[str] = None
    contenido_requerido: List[str] = Field(default_factory=list)
    es_obligatorio: bool = True


class CapituloEIAResponse(CapituloEIABase):
    """Respuesta de capítulo del EIA."""
    id: int
    tipo_proyecto_id: int
    orden: int
    activo: bool = True

    class Config:
        from_attributes = True


class CapituloConEstado(BaseModel):
    """Capítulo del EIA con estado y progreso (instancia en proyecto)."""
    numero: int
    titulo: str
    descripcion: Optional[str] = None
    contenido_requerido: List[str] = Field(default_factory=list)
    es_obligatorio: bool = True
    estado: EstadoCapituloEnum = EstadoCapituloEnum.PENDIENTE
    progreso_porcentaje: int = Field(default=0, ge=0, le=100)
    secciones_completadas: int = 0
    secciones_totales: int = 0
    notas: Optional[str] = None


# =============================================================================
# PAS con Estado (Instancia en proyecto)
# =============================================================================

class PASConEstado(BaseModel):
    """PAS requerido con estado de tramitación."""
    articulo: int = Field(..., ge=100, le=200)
    nombre: str
    organismo: str
    obligatoriedad: ObligatoriedadPASEnum
    estado: EstadoPASEnum = EstadoPASEnum.IDENTIFICADO
    condiciones: Optional[Dict[str, Any]] = None
    fecha_limite: Optional[datetime] = None
    notas: Optional[str] = None
    razon_aplicacion: Optional[str] = None


class ActualizarEstadoPAS(BaseModel):
    """Request para actualizar estado de un PAS."""
    estado: EstadoPASEnum
    notas: Optional[str] = None
    fecha_limite: Optional[datetime] = None


# =============================================================================
# Anexos Requeridos (Instancia en proyecto)
# =============================================================================

class AnexoRequerido(BaseModel):
    """Anexo técnico requerido con estado."""
    codigo: str = Field(..., max_length=20)
    nombre: str
    descripcion: Optional[str] = None
    profesional_responsable: Optional[str] = None
    obligatorio: bool = False
    estado: EstadoAnexoEnum = EstadoAnexoEnum.PENDIENTE
    condicion_activacion: Optional[Dict[str, Any]] = None
    razon_aplicacion: Optional[str] = None


class ActualizarEstadoAnexo(BaseModel):
    """Request para actualizar estado de un anexo."""
    estado: EstadoAnexoEnum
    notas: Optional[str] = None


# =============================================================================
# Componentes de Línea Base
# =============================================================================

class ComponenteLineaBaseBase(BaseModel):
    """Base para componente de línea base."""
    codigo: str = Field(..., max_length=50)
    nombre: str = Field(..., max_length=150)
    descripcion: Optional[str] = None
    metodologia: Optional[str] = None
    variables_monitorear: List[str] = Field(default_factory=list)
    estudios_requeridos: List[str] = Field(default_factory=list)
    duracion_estimada_dias: int = Field(default=30, ge=1)
    es_obligatorio: bool = True


class ComponenteLineaBaseResponse(ComponenteLineaBaseBase):
    """Respuesta de componente de línea base."""
    id: int
    tipo_proyecto_id: int
    subtipo_id: Optional[int] = None
    capitulo_numero: int = 3
    orden: int = 0
    activo: bool = True

    class Config:
        from_attributes = True


class ComponenteLineaBaseEnPlan(ComponenteLineaBaseBase):
    """Componente de línea base incluido en el plan del proyecto."""
    aplica: bool = True
    razon_aplicacion: Optional[str] = None
    prioridad: int = Field(default=1, ge=1, le=5)


# =============================================================================
# Estimación de Complejidad
# =============================================================================

class FactorComplejidad(BaseModel):
    """Factor que contribuye a la complejidad del EIA."""
    nombre: str
    descripcion: str
    peso: float = Field(..., ge=0, le=1)
    valor: float = Field(..., ge=0, le=10)
    contribucion: float = 0  # peso * valor


class RecursoSugerido(BaseModel):
    """Recurso sugerido para el EIA."""
    tipo: str  # "profesional", "estudio", "equipo"
    nombre: str
    descripcion: Optional[str] = None
    cantidad: int = 1
    prioridad: str = "alta"  # alta, media, baja


class EstimacionComplejidad(BaseModel):
    """Estimación de complejidad del EIA."""
    nivel: NivelComplejidadEnum
    puntaje: int = Field(..., ge=0, le=100)
    factores: List[FactorComplejidad] = Field(default_factory=list)
    tiempo_estimado_meses: int = Field(..., ge=1)
    recursos_sugeridos: List[RecursoSugerido] = Field(default_factory=list)
    riesgos_principales: List[str] = Field(default_factory=list)
    recomendaciones: List[str] = Field(default_factory=list)


# =============================================================================
# Estructura EIA Completa (Response principal)
# =============================================================================

class EstructuraEIABase(BaseModel):
    """Base para estructura EIA de un proyecto."""
    capitulos: List[CapituloConEstado] = Field(default_factory=list)
    pas_requeridos: List[PASConEstado] = Field(default_factory=list)
    anexos_requeridos: List[AnexoRequerido] = Field(default_factory=list)
    plan_linea_base: List[ComponenteLineaBaseEnPlan] = Field(default_factory=list)
    estimacion_complejidad: Optional[EstimacionComplejidad] = None


class EstructuraEIAResponse(EstructuraEIABase):
    """Respuesta completa de estructura EIA/DIA."""
    id: int
    proyecto_id: int
    version: int = 1
    instrumento: InstrumentoAmbientalEnum = InstrumentoAmbientalEnum.EIA
    progreso_general: int = Field(default=0, ge=0, le=100)
    capitulos_completados: int = 0
    total_capitulos: int = 0
    pas_aprobados: int = 0
    total_pas: int = 0
    notas: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class EstructuraEIAResumen(BaseModel):
    """Resumen de estructura EIA para listados."""
    id: int
    proyecto_id: int
    version: int
    progreso_general: int
    total_capitulos: int
    total_pas: int
    total_anexos: int
    nivel_complejidad: Optional[NivelComplejidadEnum] = None
    created_at: datetime


# =============================================================================
# Requests para operaciones
# =============================================================================

class GenerarEstructuraRequest(BaseModel):
    """Request para generar estructura EIA o DIA."""
    proyecto_id: int
    instrumento: InstrumentoAmbientalEnum = InstrumentoAmbientalEnum.EIA
    forzar_regenerar: bool = False


class ActualizarCapituloRequest(BaseModel):
    """Request para actualizar estado de un capítulo."""
    estado: EstadoCapituloEnum
    progreso_porcentaje: Optional[int] = Field(None, ge=0, le=100)
    notas: Optional[str] = None


class ActualizarPASRequest(BaseModel):
    """Request para actualizar estado de un PAS."""
    estado: EstadoPASEnum
    fecha_limite: Optional[datetime] = None
    notas: Optional[str] = None


class ActualizarAnexoRequest(BaseModel):
    """Request para actualizar estado de un anexo."""
    estado: EstadoAnexoEnum
    notas: Optional[str] = None


# =============================================================================
# Responses para listados de configuración
# =============================================================================

class CapitulosListResponse(BaseModel):
    """Lista de capítulos configurados para un tipo."""
    capitulos: List[CapituloEIAResponse]
    total: int
    tipo_proyecto_codigo: str


class ComponentesLineaBaseListResponse(BaseModel):
    """Lista de componentes de línea base."""
    componentes: List[ComponenteLineaBaseResponse]
    total: int
    tipo_proyecto_codigo: str
    duracion_total_dias: int


# =============================================================================
# Responses especiales para el asistente
# =============================================================================

class ResumenEstructuraParaAsistente(BaseModel):
    """Resumen de estructura EIA formateado para el asistente."""
    existe_estructura: bool = False
    proyecto_id: Optional[int] = None
    version: Optional[int] = None
    progreso_general: int = 0

    # Contadores
    capitulos_total: int = 0
    capitulos_completados: int = 0
    capitulos_en_progreso: int = 0
    capitulos_pendientes: int = 0

    pas_total: int = 0
    pas_aprobados: int = 0
    pas_en_tramite: int = 0
    pas_pendientes: int = 0

    anexos_total: int = 0
    anexos_completados: int = 0

    # Complejidad
    nivel_complejidad: Optional[str] = None
    tiempo_estimado_meses: Optional[int] = None

    # Próximos pasos sugeridos
    proximos_pasos: List[str] = Field(default_factory=list)


class CapituloDetalleParaAsistente(BaseModel):
    """Detalle de un capítulo formateado para el asistente."""
    numero: int
    titulo: str
    descripcion: Optional[str]
    estado: str
    progreso: int
    secciones: List[str]
    secciones_completadas: int
    contenido_sugerido: Optional[str] = None


# =============================================================================
# Configuración por Instrumento (EIA vs DIA)
# =============================================================================

class EstructuraPorInstrumentoBase(BaseModel):
    """Base para configuración por instrumento."""
    instrumento: InstrumentoAmbientalEnum
    capitulos_requeridos: List[int] = Field(default_factory=list)
    max_paginas_resumen: int = Field(..., ge=1)
    requiere_linea_base: bool = True
    requiere_prediccion_impactos: bool = True
    requiere_plan_mitigacion: bool = True
    requiere_plan_contingencias: bool = True
    requiere_plan_seguimiento: bool = True
    plazo_evaluacion_dias: int = Field(..., ge=1)
    plazo_prorroga_dias: int = Field(..., ge=1)
    max_icsara: int = Field(default=2, ge=1, le=3)


class EstructuraPorInstrumentoResponse(EstructuraPorInstrumentoBase):
    """Respuesta de configuración por instrumento."""
    id: int
    tipo_proyecto_id: Optional[int] = None
    activo: bool = True

    class Config:
        from_attributes = True


class ConfiguracionInstrumentoResumen(BaseModel):
    """Resumen de configuración para UI."""
    instrumento: InstrumentoAmbientalEnum
    nombre_completo: str  # "Estudio de Impacto Ambiental" o "Declaración de Impacto Ambiental"
    capitulos_requeridos: int
    requiere_linea_base: bool
    plazo_evaluacion_dias: int
    max_paginas_resumen: int
