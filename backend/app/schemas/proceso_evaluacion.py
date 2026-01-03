"""
Schemas Pydantic para Gestor de Proceso de Evaluación SEIA (ICSARA/Adendas).
"""
from datetime import date, datetime
from typing import Optional, List, Dict, Any, Literal
from enum import Enum

from pydantic import BaseModel, Field, field_validator


# =============================================================================
# ENUMS
# =============================================================================

class EstadoEvaluacion(str, Enum):
    NO_INGRESADO = "no_ingresado"
    INGRESADO = "ingresado"
    EN_ADMISIBILIDAD = "en_admisibilidad"
    ADMITIDO = "admitido"
    INADMITIDO = "inadmitido"
    EN_EVALUACION = "en_evaluacion"
    ICSARA_EMITIDO = "icsara_emitido"
    ADENDA_EN_REVISION = "adenda_en_revision"
    ICE_EMITIDO = "ice_emitido"
    EN_COMISION = "en_comision"
    RCA_APROBADA = "rca_aprobada"
    RCA_RECHAZADA = "rca_rechazada"
    DESISTIDO = "desistido"
    CADUCADO = "caducado"


class ResultadoRCA(str, Enum):
    FAVORABLE = "favorable"
    FAVORABLE_CON_CONDICIONES = "favorable_con_condiciones"
    DESFAVORABLE = "desfavorable"
    DESISTIMIENTO = "desistimiento"
    CADUCIDAD = "caducidad"


class EstadoICSARA(str, Enum):
    EMITIDO = "emitido"
    RESPONDIDO = "respondido"
    PARCIALMENTE_RESPONDIDO = "parcialmente_respondido"
    VENCIDO = "vencido"


class EstadoAdenda(str, Enum):
    EN_ELABORACION = "en_elaboracion"
    PRESENTADA = "presentada"
    EN_REVISION = "en_revision"
    ACEPTADA = "aceptada"
    CON_OBSERVACIONES = "con_observaciones"
    RECHAZADA = "rechazada"


class ResultadoRevision(str, Enum):
    SUFICIENTE = "suficiente"
    INSUFICIENTE = "insuficiente"
    PARCIALMENTE_SUFICIENTE = "parcialmente_suficiente"


class TipoObservacion(str, Enum):
    AMPLIACION = "ampliacion"
    ACLARACION = "aclaracion"
    RECTIFICACION = "rectificacion"


class PrioridadObservacion(str, Enum):
    CRITICA = "critica"
    IMPORTANTE = "importante"
    MENOR = "menor"


class EstadoObservacionICSARA(str, Enum):
    PENDIENTE = "pendiente"
    RESPONDIDA = "respondida"
    PARCIAL = "parcial"


# =============================================================================
# SCHEMAS DE OBSERVACIONES Y RESPUESTAS
# =============================================================================

class ObservacionICSARA(BaseModel):
    """Observación individual dentro de un ICSARA."""

    id: Optional[str] = Field(None, description="Identificador único, ej: OBS-001 (auto-generado si no se proporciona)")
    oaeca: str = Field(..., description="Organismo que emite la observación, ej: SERNAGEOMIN")
    capitulo_eia: int = Field(..., ge=1, le=11, description="Capítulo del EIA al que refiere")
    componente: Optional[str] = Field(None, description="Componente ambiental específico")
    tipo: TipoObservacion = Field(..., description="Tipo de solicitud")
    texto: str = Field(..., min_length=10, description="Texto de la observación")
    prioridad: PrioridadObservacion = Field(..., description="Nivel de prioridad")
    estado: EstadoObservacionICSARA = Field(
        default=EstadoObservacionICSARA.PENDIENTE,
        description="Estado de la observación"
    )

    model_config = {"use_enum_values": True}


class RespuestaAdenda(BaseModel):
    """Respuesta a una observación dentro de una Adenda."""

    observacion_id: str = Field(..., description="ID de la observación que responde")
    respuesta: str = Field(..., min_length=10, description="Texto de la respuesta")
    anexos_referenciados: List[str] = Field(default_factory=list, description="Códigos de anexos")
    estado: Literal["respondida", "parcial", "no_respondida"] = Field(
        default="respondida",
        description="Estado de la respuesta"
    )
    calificacion_sea: Optional[Literal["suficiente", "insuficiente"]] = Field(
        None,
        description="Calificación del SEA (después de revisión)"
    )

    model_config = {"use_enum_values": True}


class CondicionRCA(BaseModel):
    """Condición de una RCA favorable con condiciones."""

    numero: int = Field(..., description="Número de la condición")
    descripcion: str = Field(..., description="Descripción de la condición")
    plazo: Optional[str] = Field(None, description="Plazo de cumplimiento")
    responsable: Optional[str] = Field(None, description="Responsable del cumplimiento")


# =============================================================================
# SCHEMAS DE CREACIÓN
# =============================================================================

class ProcesoEvaluacionCreate(BaseModel):
    """Datos para iniciar un proceso de evaluación."""

    proyecto_id: int = Field(..., description="ID del proyecto")
    fecha_ingreso: date = Field(..., description="Fecha de ingreso al SEIA")
    plazo_legal_dias: int = Field(default=120, description="Plazo legal (120 EIA, 60 DIA)")

    @field_validator('plazo_legal_dias')
    @classmethod
    def validar_plazo(cls, v):
        if v not in [60, 120]:
            raise ValueError("El plazo debe ser 60 (DIA) o 120 (EIA)")
        return v


class ICSARACreate(BaseModel):
    """Datos para registrar un nuevo ICSARA."""

    numero_icsara: int = Field(..., ge=1, le=3, description="Número de ICSARA (1, 2 o excepcionalmente 3)")
    fecha_emision: date = Field(..., description="Fecha de emisión del ICSARA")
    fecha_limite_respuesta: date = Field(..., description="Fecha límite para presentar Adenda")
    observaciones: List[ObservacionICSARA] = Field(
        default_factory=list,
        description="Lista de observaciones"
    )

    @field_validator('fecha_limite_respuesta')
    @classmethod
    def validar_fecha_limite(cls, v, info):
        fecha_emision = info.data.get('fecha_emision')
        if fecha_emision and v <= fecha_emision:
            raise ValueError("La fecha límite debe ser posterior a la fecha de emisión")
        return v


class AdendaCreate(BaseModel):
    """Datos para registrar una nueva Adenda."""

    numero_adenda: int = Field(..., ge=1, description="Número de Adenda")
    fecha_presentacion: date = Field(..., description="Fecha de presentación de la Adenda")
    respuestas: List[RespuestaAdenda] = Field(
        default_factory=list,
        description="Lista de respuestas a observaciones"
    )


class ActualizarEstadoObservacion(BaseModel):
    """Datos para actualizar el estado de una observación."""

    estado: EstadoObservacionICSARA = Field(..., description="Nuevo estado")
    calificacion: Optional[Literal["suficiente", "insuficiente"]] = Field(
        None,
        description="Calificación del SEA (opcional)"
    )


class RegistrarRCA(BaseModel):
    """Datos para registrar la RCA final."""

    resultado: ResultadoRCA = Field(..., description="Resultado de la RCA")
    numero_rca: str = Field(..., description="Número de la RCA")
    fecha: date = Field(..., description="Fecha de la RCA")
    condiciones: Optional[List[CondicionRCA]] = Field(
        None,
        description="Condiciones (si es favorable con condiciones)"
    )
    url: Optional[str] = Field(None, description="URL del documento RCA")

    model_config = {"use_enum_values": True}


class RegistrarAdmisibilidad(BaseModel):
    """Datos para registrar resultado de admisibilidad."""

    resultado: Literal["admitido", "inadmitido"] = Field(..., description="Resultado")
    fecha: date = Field(..., description="Fecha del pronunciamiento")
    observaciones: Optional[str] = Field(None, description="Observaciones (si inadmitido)")


# =============================================================================
# SCHEMAS DE RESPUESTA
# =============================================================================

class AdendaResponse(BaseModel):
    """Respuesta completa de una Adenda."""

    id: int
    icsara_id: int
    numero_adenda: int
    fecha_presentacion: date
    respuestas: List[Dict[str, Any]]
    total_respuestas: int
    observaciones_resueltas: int
    observaciones_pendientes: int
    porcentaje_resueltas: float
    estado: str
    fecha_revision: Optional[date]
    resultado_revision: Optional[str]
    archivo_id: Optional[int]
    created_at: Optional[datetime]

    model_config = {"from_attributes": True}


class ICSARAResponse(BaseModel):
    """Respuesta completa de un ICSARA."""

    id: int
    proceso_evaluacion_id: int
    numero_icsara: int
    fecha_emision: date
    fecha_limite_respuesta: date
    dias_para_responder: int
    esta_vencido: bool
    observaciones: List[Dict[str, Any]]
    total_observaciones: int
    observaciones_resueltas: int
    observaciones_pendientes: int
    observaciones_por_oaeca: Dict[str, int]
    estado: str
    archivo_id: Optional[int]
    adendas: List[AdendaResponse]
    created_at: Optional[datetime]

    model_config = {"from_attributes": True}


class ProcesoEvaluacionResponse(BaseModel):
    """Respuesta completa de un proceso de evaluación."""

    id: int
    proyecto_id: int
    estado_evaluacion: str
    fecha_ingreso: Optional[date]
    fecha_admisibilidad: Optional[date]
    fecha_rca: Optional[date]
    resultado_rca: Optional[str]
    plazo_legal_dias: int
    dias_transcurridos: int
    dias_suspension: int
    dias_restantes: int
    porcentaje_plazo: float
    numero_rca: Optional[str]
    url_rca: Optional[str]
    condiciones_rca: Optional[List[Dict[str, Any]]]
    total_icsara: int
    total_observaciones: int
    observaciones_pendientes: int
    icsaras: List[ICSARAResponse]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


class ResumenProcesoEvaluacion(BaseModel):
    """Resumen del proceso de evaluación para vista rápida."""

    proyecto_id: int
    proyecto_nombre: Optional[str] = None
    estado_actual: str
    estado_label: str
    fecha_ingreso: Optional[date]
    dias_transcurridos: int
    dias_restantes: int
    porcentaje_plazo: float

    # ICSARA
    total_icsara: int
    icsara_actual: Optional[int]
    observaciones_totales: int
    observaciones_pendientes: int
    observaciones_resueltas: int

    # Por OAECA
    observaciones_por_oaeca: Dict[str, int]
    oaeca_criticos: List[str]  # Organismos con más observaciones

    # Adendas
    total_adendas: int
    ultima_adenda_fecha: Optional[date]

    # Próximos pasos
    proxima_accion: str
    fecha_limite: Optional[date]
    alerta: Optional[str]

    model_config = {"from_attributes": True}


class PlazoEvaluacion(BaseModel):
    """Información de plazos del proceso."""

    plazo_legal_dias: int
    dias_transcurridos: int
    dias_suspension: int
    dias_efectivos: int
    dias_restantes: int
    porcentaje_transcurrido: float
    estado_plazo: Literal["normal", "alerta", "critico", "vencido"]
    fecha_limite_estimada: Optional[date]


class EstadoTimeline(BaseModel):
    """Estado para el timeline de evaluación."""

    id: str
    nombre: str
    descripcion: str
    estado: Literal["completado", "actual", "pendiente"]
    fecha: Optional[date]
    icono: Optional[str]


class TimelineEvaluacion(BaseModel):
    """Timeline completo del proceso de evaluación."""

    proyecto_id: int
    estados: List[EstadoTimeline]
    estado_actual: str
    progreso_porcentaje: int


# =============================================================================
# SCHEMAS DE ESTADÍSTICAS
# =============================================================================

class EstadisticasICSARA(BaseModel):
    """Estadísticas de observaciones ICSARA."""

    total_observaciones: int
    por_tipo: Dict[str, int]  # ampliacion, aclaracion, rectificacion
    por_prioridad: Dict[str, int]  # critica, importante, menor
    por_oaeca: Dict[str, int]
    por_capitulo: Dict[int, int]
    por_estado: Dict[str, int]
    oaeca_mas_observaciones: str
    capitulo_mas_observaciones: int


class EstadisticasProceso(BaseModel):
    """Estadísticas generales del proceso."""

    proyecto_id: int
    dias_en_evaluacion: int
    total_icsara: int
    total_adendas: int
    observaciones_totales: int
    observaciones_resueltas: int
    tasa_resolucion: float
    tiempo_promedio_respuesta_dias: Optional[int]
