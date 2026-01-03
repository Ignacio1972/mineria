"""
Schemas Pydantic para la Ficha Acumulativa del Proyecto.

Define DTOs para características, ubicaciones, diagnósticos
y la ficha consolidada del proyecto.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field, field_validator


# =============================================================================
# Enums
# =============================================================================

class CategoriaCaracteristica(str, Enum):
    """Categorías de características del proyecto."""
    IDENTIFICACION = "identificacion"
    TECNICO = "tecnico"
    OBRAS = "obras"
    FASES = "fases"
    INSUMOS = "insumos"
    EMISIONES = "emisiones"
    SOCIAL = "social"
    AMBIENTAL = "ambiental"


class FuenteDatoEnum(str, Enum):
    """Origen del dato."""
    MANUAL = "manual"
    ASISTENTE = "asistente"
    DOCUMENTO = "documento"
    GIS = "gis"


class EstadoPASEnum(str, Enum):
    """Estado de tramitación de un PAS."""
    IDENTIFICADO = "identificado"
    REQUERIDO = "requerido"
    NO_APLICA = "no_aplica"
    EN_TRAMITE = "en_tramite"
    APROBADO = "aprobado"
    RECHAZADO = "rechazado"


class EstadoLiteralArt11(str, Enum):
    """Estado del análisis de literal Art. 11."""
    PENDIENTE = "pendiente"
    NO_APLICA = "no_aplica"
    PROBABLE = "probable"
    CONFIRMADO = "confirmado"


class ViaSugeridaEnum(str, Enum):
    """Vía de ingreso sugerida."""
    DIA = "DIA"
    EIA = "EIA"
    NO_SEIA = "NO_SEIA"
    INDEFINIDO = "INDEFINIDO"


# =============================================================================
# Características (Ficha Acumulativa)
# =============================================================================

class CaracteristicaBase(BaseModel):
    """Base para características del proyecto."""
    categoria: CategoriaCaracteristica
    clave: str = Field(..., min_length=1, max_length=100)
    valor: Optional[str] = None
    valor_numerico: Optional[float] = None
    unidad: Optional[str] = Field(None, max_length=50)
    notas: Optional[str] = None


class CaracteristicaCreate(CaracteristicaBase):
    """Crear característica."""
    fuente: FuenteDatoEnum = FuenteDatoEnum.MANUAL
    pregunta_codigo: Optional[str] = None


class CaracteristicaUpdate(BaseModel):
    """Actualizar característica."""
    valor: Optional[str] = None
    valor_numerico: Optional[float] = None
    unidad: Optional[str] = None
    fuente: Optional[FuenteDatoEnum] = None
    notas: Optional[str] = None
    validado: Optional[bool] = None


class CaracteristicaResponse(CaracteristicaBase):
    """Respuesta de característica."""
    id: int
    proyecto_id: int
    fuente: FuenteDatoEnum
    pregunta_codigo: Optional[str] = None
    validado: bool = False
    validado_por: Optional[str] = None
    validado_fecha: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CaracteristicaBulkCreate(BaseModel):
    """Crear múltiples características de una vez."""
    caracteristicas: List[CaracteristicaCreate]
    fuente: FuenteDatoEnum = FuenteDatoEnum.ASISTENTE


class CaracteristicasByCategoriaResponse(BaseModel):
    """Características agrupadas por categoría."""
    identificacion: Dict[str, Any] = {}
    tecnico: Dict[str, Any] = {}
    obras: Dict[str, Any] = {}
    fases: Dict[str, Any] = {}
    insumos: Dict[str, Any] = {}
    emisiones: Dict[str, Any] = {}
    social: Dict[str, Any] = {}
    ambiental: Dict[str, Any] = {}


# =============================================================================
# Ubicación
# =============================================================================

class UbicacionBase(BaseModel):
    """Base para ubicación del proyecto."""
    regiones: Optional[List[str]] = None
    provincias: Optional[List[str]] = None
    comunas: Optional[List[str]] = None
    alcance: Optional[str] = None
    superficie_ha: Optional[float] = None


class UbicacionResponse(UbicacionBase):
    """Respuesta de ubicación."""
    id: int
    proyecto_id: int
    version: int
    es_vigente: bool
    fuente: str
    analisis_gis_cache: Optional[Dict[str, Any]] = None
    analisis_gis_fecha: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# PAS del Proyecto
# =============================================================================

class PASProyectoBase(BaseModel):
    """Base para PAS del proyecto."""
    articulo: int = Field(..., ge=100, le=200)
    nombre: str = Field(..., min_length=5, max_length=200)
    organismo: str = Field(..., min_length=2, max_length=100)
    obligatorio: bool = False
    justificacion: Optional[str] = None


class PASProyectoCreate(PASProyectoBase):
    """Crear PAS del proyecto."""
    estado: EstadoPASEnum = EstadoPASEnum.IDENTIFICADO
    condicion_activada: Optional[Dict[str, Any]] = None


class PASProyectoUpdate(BaseModel):
    """Actualizar PAS del proyecto."""
    estado: Optional[EstadoPASEnum] = None
    obligatorio: Optional[bool] = None
    justificacion: Optional[str] = None
    numero_resolucion: Optional[str] = None


class PASProyectoResponse(PASProyectoBase):
    """Respuesta de PAS del proyecto."""
    id: int
    proyecto_id: int
    estado: EstadoPASEnum
    condicion_activada: Optional[Dict[str, Any]] = None
    identificado_por: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# Análisis Art. 11
# =============================================================================

class AnalisisArt11Base(BaseModel):
    """Base para análisis de literal Art. 11."""
    literal: str = Field(..., pattern='^[a-f]$')
    estado: EstadoLiteralArt11 = EstadoLiteralArt11.PENDIENTE
    justificacion: Optional[str] = None
    confianza: Optional[int] = Field(None, ge=0, le=100)


class AnalisisArt11Create(AnalisisArt11Base):
    """Crear análisis Art. 11."""
    evidencias: Optional[List[Dict[str, Any]]] = None
    fuente_gis: bool = False
    fuente_usuario: bool = False
    fuente_asistente: bool = False


class AnalisisArt11Update(BaseModel):
    """Actualizar análisis Art. 11."""
    estado: Optional[EstadoLiteralArt11] = None
    justificacion: Optional[str] = None
    confianza: Optional[int] = Field(None, ge=0, le=100)
    evidencias: Optional[List[Dict[str, Any]]] = None


class AnalisisArt11Response(AnalisisArt11Base):
    """Respuesta de análisis Art. 11."""
    id: int
    proyecto_id: int
    evidencias: List[Dict[str, Any]] = []
    fuente_gis: bool
    fuente_usuario: bool
    fuente_asistente: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# Diagnóstico
# =============================================================================

class DiagnosticoBase(BaseModel):
    """Base para diagnóstico."""
    via_sugerida: Optional[ViaSugeridaEnum] = None
    confianza: Optional[int] = Field(None, ge=0, le=100)
    resumen: Optional[str] = None


class DiagnosticoResponse(DiagnosticoBase):
    """Respuesta de diagnóstico."""
    id: int
    proyecto_id: int
    version: int
    literales_gatillados: List[str] = []
    cumple_umbral_seia: Optional[bool] = None
    umbral_evaluado: Optional[Dict[str, Any]] = None
    permisos_identificados: List[Dict[str, Any]] = []
    alertas: List[Dict[str, Any]] = []
    recomendaciones: List[Dict[str, Any]] = []
    generado_por: str
    created_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# Ficha Consolidada
# =============================================================================

class FichaProyectoResponse(BaseModel):
    """Ficha consolidada del proyecto con todos los datos."""
    proyecto_id: int
    nombre: str
    estado: str

    # Tipo de proyecto
    tipo_codigo: Optional[str] = None
    tipo_nombre: Optional[str] = None
    subtipo_codigo: Optional[str] = None
    subtipo_nombre: Optional[str] = None

    # Ubicación
    ubicacion: Optional[UbicacionResponse] = None

    # Características por categoría
    caracteristicas: CaracteristicasByCategoriaResponse

    # Análisis Art. 11
    analisis_art11: Dict[str, AnalisisArt11Response] = {}

    # Diagnóstico actual
    diagnostico_actual: Optional[DiagnosticoResponse] = None

    # PAS identificados
    pas: List[PASProyectoResponse] = []

    # Estadísticas
    total_caracteristicas: int = 0
    caracteristicas_validadas: int = 0
    progreso_porcentaje: int = 0

    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class FichaResumenResponse(BaseModel):
    """Resumen de la ficha para listados."""
    proyecto_id: int
    nombre: str
    estado: str
    tipo_nombre: Optional[str] = None
    via_sugerida: Optional[str] = None
    progreso_porcentaje: int = 0
    total_pas: int = 0
    has_ubicacion: bool = False


# =============================================================================
# Progreso
# =============================================================================

class ProgresoFichaResponse(BaseModel):
    """Progreso de completitud de la ficha."""
    proyecto_id: int
    total_campos: int
    campos_completados: int
    campos_validados: int
    porcentaje_completitud: float
    porcentaje_validacion: float

    por_categoria: Dict[str, Dict[str, int]] = {}
    campos_faltantes_obligatorios: List[str] = []


# =============================================================================
# Acciones del Asistente
# =============================================================================

class GuardarRespuestaAsistente(BaseModel):
    """Datos para guardar respuesta del asistente en la ficha."""
    categoria: CategoriaCaracteristica
    clave: str
    valor: Optional[str] = None
    valor_numerico: Optional[float] = None
    unidad: Optional[str] = None
    pregunta_codigo: Optional[str] = None

    @field_validator('valor', 'valor_numerico')
    @classmethod
    def al_menos_un_valor(cls, v, info):
        """Valida que haya al menos un valor."""
        # Se valida después de tener todos los campos
        return v


class GuardarRespuestasAsistenteRequest(BaseModel):
    """Request para guardar múltiples respuestas del asistente."""
    proyecto_id: int
    respuestas: List[GuardarRespuestaAsistente]


class GuardarRespuestasAsistenteResponse(BaseModel):
    """Response después de guardar respuestas."""
    guardadas: int
    actualizadas: int
    errores: List[Dict[str, str]] = []
    caracteristicas: List[CaracteristicaResponse] = []
