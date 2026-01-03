"""
Schemas Pydantic para Recopilacion Guiada (Fase 3).
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator


# =============================================================================
# ENUMS
# =============================================================================

class EstadoSeccion(str, Enum):
    """Estados posibles de una seccion del EIA."""
    PENDIENTE = "pendiente"
    EN_PROGRESO = "en_progreso"
    COMPLETADO = "completado"
    VALIDADO = "validado"


class TipoRespuesta(str, Enum):
    """Tipos de respuesta para preguntas."""
    TEXTO = "texto"
    NUMERO = "numero"
    FECHA = "fecha"
    SELECCION = "seleccion"
    SELECCION_MULTIPLE = "seleccion_multiple"
    ARCHIVO = "archivo"
    COORDENADAS = "coordenadas"
    TABLA = "tabla"
    BOOLEANO = "booleano"


class SeveridadInconsistencia(str, Enum):
    """Niveles de severidad."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class EstadoExtraccion(str, Enum):
    """Estados de extraccion."""
    PENDIENTE = "pendiente"
    PROCESANDO = "procesando"
    COMPLETADO = "completado"
    ERROR = "error"


# =============================================================================
# SCHEMAS DE PREGUNTAS
# =============================================================================

class OpcionSeleccion(BaseModel):
    """Opcion para preguntas de tipo seleccion."""
    valor: str
    etiqueta: str
    descripcion: Optional[str] = None


class ValidacionPregunta(BaseModel):
    """Reglas de validacion para una pregunta."""
    requerido: bool = True
    min: Optional[Union[int, float]] = None
    max: Optional[Union[int, float]] = None
    patron: Optional[str] = None
    mensaje_patron: Optional[str] = None


class PreguntaRecopilacionBase(BaseModel):
    """Schema base para preguntas de recopilacion."""
    capitulo_numero: int
    seccion_codigo: str
    seccion_nombre: Optional[str] = None
    codigo_pregunta: str
    pregunta: str
    descripcion: Optional[str] = None
    tipo_respuesta: TipoRespuesta = TipoRespuesta.TEXTO
    opciones: Optional[List[OpcionSeleccion]] = None
    valor_por_defecto: Optional[Any] = None
    validaciones: Optional[ValidacionPregunta] = None
    es_obligatoria: bool = True
    orden: int = 0


class PreguntaRecopilacionResponse(PreguntaRecopilacionBase):
    """Respuesta de pregunta de recopilacion."""
    id: int
    condicion_activacion: Optional[Dict[str, Any]] = None
    activo: bool = True

    class Config:
        from_attributes = True


class PreguntaConRespuesta(PreguntaRecopilacionResponse):
    """Pregunta con su respuesta actual."""
    respuesta_actual: Optional[Any] = None
    es_valida: bool = True
    mensaje_validacion: Optional[str] = None


# =============================================================================
# SCHEMAS DE SECCIONES
# =============================================================================

class SeccionBase(BaseModel):
    """Schema base para secciones."""
    capitulo_numero: int
    seccion_codigo: str
    seccion_nombre: Optional[str] = None


class SeccionConPreguntas(SeccionBase):
    """Seccion con sus preguntas."""
    preguntas: List[PreguntaConRespuesta] = []
    total_preguntas: int = 0
    preguntas_obligatorias: int = 0
    preguntas_respondidas: int = 0
    progreso: int = 0
    estado: EstadoSeccion = EstadoSeccion.PENDIENTE


class SeccionResumen(SeccionBase):
    """Resumen de estado de una seccion."""
    estado: EstadoSeccion
    progreso: int
    tiene_inconsistencias: bool = False
    documentos_vinculados: int = 0


# =============================================================================
# SCHEMAS DE CONTENIDO
# =============================================================================

class ContenidoEIABase(BaseModel):
    """Schema base para contenido EIA."""
    capitulo_numero: int
    seccion_codigo: str
    seccion_nombre: Optional[str] = None


class ContenidoEIACreate(ContenidoEIABase):
    """Schema para crear contenido EIA."""
    contenido: Dict[str, Any] = Field(default_factory=dict)


class ContenidoEIAUpdate(BaseModel):
    """Schema para actualizar contenido EIA."""
    contenido: Optional[Dict[str, Any]] = None
    estado: Optional[EstadoSeccion] = None
    notas: Optional[str] = None


class RespuestaIndividual(BaseModel):
    """Schema para guardar una respuesta individual."""
    codigo_pregunta: str
    valor: Any


class GuardarRespuestasRequest(BaseModel):
    """Request para guardar multiples respuestas."""
    respuestas: List[RespuestaIndividual]


class ContenidoEIAResponse(ContenidoEIABase):
    """Respuesta de contenido EIA."""
    id: int
    proyecto_id: int
    contenido: Dict[str, Any] = Field(default_factory=dict)
    estado: EstadoSeccion
    progreso: int
    documentos_vinculados: List[int] = []
    validaciones: List[Dict[str, Any]] = []
    inconsistencias: List[Dict[str, Any]] = []
    sugerencias: List[Dict[str, Any]] = []
    notas: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# =============================================================================
# SCHEMAS DE INCONSISTENCIAS
# =============================================================================

class InconsistenciaDetectada(BaseModel):
    """Inconsistencia detectada entre secciones."""
    regla_codigo: str
    regla_nombre: str
    capitulo_origen: int
    seccion_origen: str
    campo_origen: str
    valor_origen: Optional[Any] = None
    capitulo_destino: int
    seccion_destino: str
    campo_destino: str
    valor_destino: Optional[Any] = None
    mensaje: str
    severidad: SeveridadInconsistencia
    fecha_deteccion: Optional[datetime] = None


class ValidacionConsistenciaResponse(BaseModel):
    """Resultado de validacion de consistencia."""
    proyecto_id: int
    total_reglas_evaluadas: int
    inconsistencias: List[InconsistenciaDetectada]
    errores: int = 0
    warnings: int = 0
    es_consistente: bool

    @validator('es_consistente', always=True, pre=True)
    def calcular_consistencia(cls, v, values):
        return values.get('errores', 0) == 0


# =============================================================================
# SCHEMAS DE CAPITULOS
# =============================================================================

class CapituloProgreso(BaseModel):
    """Progreso de un capitulo."""
    numero: int
    titulo: str
    total_secciones: int
    secciones_completadas: int
    progreso: int
    estado: EstadoSeccion
    tiene_inconsistencias: bool = False
    secciones: List[SeccionResumen] = []


class ProgresoGeneralEIA(BaseModel):
    """Progreso general del EIA."""
    proyecto_id: int
    total_capitulos: int
    capitulos_completados: int
    progreso_general: int
    total_inconsistencias: int
    capitulos: List[CapituloProgreso]


# =============================================================================
# SCHEMAS DE EXTRACCION
# =============================================================================

class MapeoSeccionSugerido(BaseModel):
    """Mapeo sugerido de dato extraido a seccion."""
    capitulo_numero: int
    seccion_codigo: str
    campo: str
    valor: Any
    confianza: float = Field(ge=0.0, le=1.0)


class ExtraccionDocumentoBase(BaseModel):
    """Schema base para extraccion de documento."""
    documento_id: int
    tipo_documento: Optional[str] = None


class ExtraccionDocumentoRequest(ExtraccionDocumentoBase):
    """Request para extraer datos de documento."""
    forzar_reprocesar: bool = False


class ExtraccionDocumentoResponse(ExtraccionDocumentoBase):
    """Respuesta de extraccion de documento."""
    id: int
    proyecto_id: int
    datos_extraidos: Dict[str, Any] = Field(default_factory=dict)
    mapeo_secciones: List[MapeoSeccionSugerido] = []
    confianza_extraccion: float = 0.0
    estado: EstadoExtraccion
    errores: List[Dict[str, Any]] = []
    procesado_por: str = "claude_vision"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AplicarExtraccionRequest(BaseModel):
    """Request para aplicar datos extraidos a secciones."""
    extraccion_id: int
    mapeos_confirmados: List[MapeoSeccionSugerido]


# =============================================================================
# SCHEMAS DE VINCULACION DE DOCUMENTOS
# =============================================================================

class VincularDocumentoRequest(BaseModel):
    """Request para vincular documento a seccion."""
    documento_id: int
    capitulo_numero: int
    seccion_codigo: str


class DesvincularDocumentoRequest(BaseModel):
    """Request para desvincular documento de seccion."""
    documento_id: int
    capitulo_numero: int
    seccion_codigo: str


# =============================================================================
# SCHEMAS DE SUGERENCIAS
# =============================================================================

class SugerenciaRedaccion(BaseModel):
    """Sugerencia de redaccion para una seccion."""
    seccion_codigo: str
    campo: str
    texto_sugerido: str
    fuente: str  # corpus_sea, eia_aprobado, etc.
    confianza: float = Field(ge=0.0, le=1.0)


class SolicitudSugerenciaRequest(BaseModel):
    """Request para obtener sugerencias de redaccion."""
    capitulo_numero: int
    seccion_codigo: str
    campo: Optional[str] = None
    contexto_adicional: Optional[str] = None


class SugerenciasResponse(BaseModel):
    """Respuesta con sugerencias de redaccion."""
    sugerencias: List[SugerenciaRedaccion]
    total: int


# =============================================================================
# SCHEMAS DE INICIALIZACION
# =============================================================================

class IniciarCapituloRequest(BaseModel):
    """Request para iniciar recopilacion de un capitulo."""
    capitulo_numero: int


class IniciarCapituloResponse(BaseModel):
    """Respuesta al iniciar recopilacion de un capitulo."""
    capitulo_numero: int
    titulo: str
    secciones: List[SeccionConPreguntas]
    total_preguntas: int
    preguntas_obligatorias: int
    mensaje_bienvenida: str
