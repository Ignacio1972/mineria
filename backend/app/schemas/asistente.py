"""
Schemas Pydantic para el Asistente IA.
"""
from uuid import UUID
from datetime import datetime
from typing import Optional, List, Any, Literal
from enum import Enum
from pydantic import BaseModel, Field


# =============================================================================
# Enums
# =============================================================================

class RolMensaje(str, Enum):
    """Roles posibles de un mensaje."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class EstadoAccion(str, Enum):
    """Estados posibles de una accion pendiente."""
    PENDIENTE = "pendiente"
    CONFIRMADA = "confirmada"
    CANCELADA = "cancelada"
    EXPIRADA = "expirada"
    EJECUTADA = "ejecutada"
    ERROR = "error"


class TipoAccion(str, Enum):
    """Tipos de acciones que puede ejecutar el asistente."""
    CREAR_PROYECTO = "crear_proyecto"
    ACTUALIZAR_PROYECTO = "actualizar_proyecto"
    EJECUTAR_ANALISIS = "ejecutar_analisis"
    EXPORTAR_INFORME = "exportar_informe"
    NAVEGAR = "navegar"


# =============================================================================
# Tool Calls (formato Anthropic)
# =============================================================================

class ToolCallInput(BaseModel):
    """Entrada de una llamada a herramienta."""
    pass


class ToolCall(BaseModel):
    """Llamada a una herramienta del agente."""
    id: str
    name: str
    input: dict = Field(default_factory=dict)


class ToolResult(BaseModel):
    """Resultado de una herramienta."""
    tool_call_id: str
    tool_name: str
    content: Any
    is_error: bool = False


# =============================================================================
# Fuentes citadas
# =============================================================================

class FuenteCitada(BaseModel):
    """Fuente citada en una respuesta del asistente."""
    tipo: str  # legal, sistema, web
    titulo: str
    referencia: Optional[str] = None  # articulo, seccion, URL
    fragmento: Optional[str] = None
    confianza: Optional[float] = None
    # Campos para acceso al documento original
    documento_id: Optional[int] = None
    url_documento: Optional[str] = None  # URL para ver el documento en el visor
    url_descarga: Optional[str] = None  # URL para descargar el PDF directamente


# =============================================================================
# Mensajes
# =============================================================================

class MensajeBase(BaseModel):
    """Base para mensajes."""
    contenido: str = Field(..., min_length=1)


class MensajeUsuario(MensajeBase):
    """Mensaje enviado por el usuario."""
    proyecto_contexto_id: Optional[int] = None
    vista_actual: Optional[str] = None


class MensajeAsistente(MensajeBase):
    """Mensaje del asistente."""
    tool_calls: Optional[List[ToolCall]] = None
    fuentes: Optional[List[FuenteCitada]] = None
    tokens_input: Optional[int] = None
    tokens_output: Optional[int] = None
    latencia_ms: Optional[int] = None
    modelo_usado: Optional[str] = None


class MensajeTool(MensajeBase):
    """Mensaje de resultado de herramienta."""
    tool_call_id: str
    tool_name: str


class MensajeResponse(BaseModel):
    """Respuesta de mensaje para API."""
    id: UUID
    conversacion_id: UUID
    rol: RolMensaje
    contenido: str
    tool_calls: Optional[List[ToolCall]] = None
    fuentes: Optional[List[FuenteCitada]] = None
    tokens_input: Optional[int] = None
    tokens_output: Optional[int] = None
    latencia_ms: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# Acciones pendientes
# =============================================================================

class AccionPendienteBase(BaseModel):
    """Base para acciones pendientes."""
    tipo: TipoAccion
    parametros: dict = Field(default_factory=dict)
    descripcion: str


class AccionPendienteCreate(AccionPendienteBase):
    """Crear una accion pendiente."""
    conversacion_id: UUID
    mensaje_id: Optional[UUID] = None


class AccionPendienteResponse(AccionPendienteBase):
    """Respuesta de accion pendiente."""
    id: UUID
    conversacion_id: UUID
    estado: EstadoAccion
    resultado: Optional[dict] = None
    error_mensaje: Optional[str] = None
    created_at: datetime
    expires_at: datetime
    puede_confirmarse: bool = True

    class Config:
        from_attributes = True


class ConfirmacionAccion(BaseModel):
    """Solicitud de confirmacion/cancelacion de accion."""
    accion_id: UUID
    confirmada: bool
    comentario: Optional[str] = None


class ResultadoAccion(BaseModel):
    """Resultado de ejecutar una accion."""
    exito: bool
    mensaje: str
    datos: Optional[dict] = None
    error: Optional[str] = None


# =============================================================================
# Conversaciones
# =============================================================================

class ConversacionCreate(BaseModel):
    """Crear una nueva conversacion."""
    session_id: UUID
    user_id: Optional[UUID] = None
    proyecto_activo_id: Optional[int] = None
    titulo: Optional[str] = None


class ConversacionUpdate(BaseModel):
    """Actualizar conversacion."""
    titulo: Optional[str] = None
    proyecto_activo_id: Optional[int] = None
    vista_actual: Optional[str] = None
    activa: Optional[bool] = None


class ConversacionResponse(BaseModel):
    """Respuesta de conversacion."""
    id: UUID
    session_id: UUID
    user_id: Optional[UUID] = None
    titulo: Optional[str] = None
    proyecto_activo_id: Optional[int] = None
    proyecto_nombre: Optional[str] = None
    vista_actual: str = "dashboard"
    activa: bool = True
    total_mensajes: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConversacionConMensajes(ConversacionResponse):
    """Conversacion con historial de mensajes."""
    mensajes: List[MensajeResponse] = []


# =============================================================================
# Chat Request/Response
# =============================================================================

class ChatRequest(BaseModel):
    """Solicitud de chat."""
    mensaje: str = Field(..., min_length=1, max_length=4000)
    conversacion_id: Optional[UUID] = None
    session_id: UUID
    user_id: Optional[UUID] = None
    proyecto_contexto_id: Optional[int] = None
    vista_actual: Optional[str] = "dashboard"


class ChatResponse(BaseModel):
    """Respuesta del chat."""
    conversacion_id: UUID
    mensaje: MensajeResponse
    accion_pendiente: Optional[AccionPendienteResponse] = None
    sugerencias: List[str] = []
    contexto_actualizado: bool = False


class ChatStreamChunk(BaseModel):
    """Chunk de respuesta en streaming."""
    tipo: Literal["texto", "tool_start", "tool_end", "done", "error"]
    contenido: Optional[str] = None
    tool_call: Optional[ToolCall] = None
    tool_result: Optional[dict] = None
    error: Optional[str] = None


# =============================================================================
# Notificaciones proactivas
# =============================================================================

class NotificacionProactiva(BaseModel):
    """Notificacion proactiva del asistente."""
    id: UUID
    trigger_codigo: str
    mensaje: str
    proyecto_id: Optional[int] = None
    proyecto_nombre: Optional[str] = None
    accion_sugerida: Optional[str] = None
    accion_parametros: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True


class NotificacionMarcarLeida(BaseModel):
    """Marcar notificacion como leida."""
    notificacion_id: UUID
    accion_tomada: Optional[str] = None


# =============================================================================
# Feedback
# =============================================================================

class FeedbackCreate(BaseModel):
    """Crear feedback sobre un mensaje."""
    mensaje_id: UUID
    valoracion: Optional[int] = Field(None, ge=1, le=5)
    es_util: Optional[bool] = None
    comentario: Optional[str] = None
    categorias_problema: List[str] = []


class FeedbackResponse(BaseModel):
    """Respuesta de feedback."""
    id: UUID
    mensaje_id: UUID
    valoracion: Optional[int] = None
    es_util: Optional[bool] = None
    comentario: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# Contexto del asistente
# =============================================================================

class ContextoAsistente(BaseModel):
    """Contexto actual del asistente para el prompt."""
    session_id: UUID
    user_id: Optional[UUID] = None
    usuario_nombre: Optional[str] = None

    # Proyecto activo
    proyecto_id: Optional[int] = None
    proyecto_nombre: Optional[str] = None
    proyecto_estado: Optional[str] = None
    proyecto_tiene_geometria: bool = False
    proyecto_tiene_analisis: bool = False

    # Vista actual
    vista_actual: str = "dashboard"

    # Historial resumido
    resumen_conversacion: Optional[str] = None

    # Acciones pendientes
    acciones_pendientes: int = 0


# =============================================================================
# Herramientas disponibles
# =============================================================================

class HerramientaInfo(BaseModel):
    """Informacion sobre una herramienta."""
    name: str
    description: str
    categoria: str
    requiere_confirmacion: bool = False
    permisos_requeridos: List[str] = []


class HerramientasDisponibles(BaseModel):
    """Lista de herramientas disponibles."""
    herramientas: List[HerramientaInfo]
    total: int


# =============================================================================
# Busqueda en corpus
# =============================================================================

class BusquedaCorpusRequest(BaseModel):
    """Solicitud de busqueda en corpus RAG."""
    query: str = Field(..., min_length=3)
    origen: Optional[Literal["legal", "sistema"]] = None
    top_k: int = Field(10, ge=1, le=50)
    temas: Optional[List[str]] = None


class FragmentoCorpus(BaseModel):
    """Fragmento del corpus."""
    id: str
    origen: str
    contenido: str
    metadata: dict
    similitud: float


class BusquedaCorpusResponse(BaseModel):
    """Respuesta de busqueda en corpus."""
    query: str
    fragmentos: List[FragmentoCorpus]
    total: int
    tiempo_ms: int


# =============================================================================
# Metricas
# =============================================================================

class MetricasAsistente(BaseModel):
    """Metricas de uso del asistente."""
    fecha: datetime
    conversaciones: int
    usuarios_unicos: int
    mensajes_usuario: int
    mensajes_asistente: int
    llamadas_herramientas: int
    avg_tokens_input: Optional[float] = None
    avg_tokens_output: Optional[float] = None
    avg_latencia_ms: Optional[float] = None


class MetricasResumen(BaseModel):
    """Resumen de metricas."""
    periodo: str
    metricas: List[MetricasAsistente]
    totales: dict


# =============================================================================
# WebSocket
# =============================================================================

class WebSocketMessage(BaseModel):
    """Mensaje WebSocket."""
    tipo: Literal["chat", "notificacion", "accion", "typing", "ping", "pong", "error"]
    payload: Optional[dict] = None


class WebSocketChatMessage(BaseModel):
    """Mensaje de chat via WebSocket."""
    mensaje: str
    proyecto_contexto_id: Optional[int] = None


class WebSocketNotificacion(BaseModel):
    """Notificacion via WebSocket."""
    notificacion: NotificacionProactiva


class WebSocketTyping(BaseModel):
    """Indicador de typing."""
    is_typing: bool
    mensaje_parcial: Optional[str] = None
