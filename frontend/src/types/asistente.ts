/**
 * Tipos para el Asistente IA.
 */

// Enums
export type RolMensaje = 'user' | 'assistant' | 'system' | 'tool'
export type EstadoAccion = 'pendiente' | 'confirmada' | 'cancelada' | 'expirada' | 'ejecutada' | 'error'
export type TipoAccion = 'crear_proyecto' | 'actualizar_proyecto' | 'ejecutar_analisis' | 'exportar_informe' | 'navegar'

// Tool Calls
export interface ToolCall {
  id: string
  name: string
  input: Record<string, unknown>
}

export interface ToolResult {
  tool_call_id: string
  tool_name: string
  content: unknown
  is_error: boolean
}

// Fuentes citadas
export interface FuenteCitada {
  tipo: string
  titulo: string
  referencia?: string
  fragmento?: string
  confianza?: number
}

// Mensajes
export interface MensajeBase {
  contenido: string
}

export interface MensajeUsuario extends MensajeBase {
  proyecto_contexto_id?: number
  vista_actual?: string
}

export interface MensajeResponse {
  id: string
  conversacion_id: string
  rol: RolMensaje
  contenido: string
  tool_calls?: ToolCall[]
  fuentes?: FuenteCitada[]
  tokens_input?: number
  tokens_output?: number
  latencia_ms?: number
  created_at: string
}

// Acciones pendientes
export interface AccionPendiente {
  id: string
  conversacion_id: string
  tipo: TipoAccion
  parametros: Record<string, unknown>
  descripcion: string
  estado: EstadoAccion
  resultado?: Record<string, unknown>
  error_mensaje?: string
  created_at: string
  expires_at: string
  puede_confirmarse: boolean
}

export interface ConfirmacionAccion {
  accion_id: string
  confirmada: boolean
  comentario?: string
}

export interface ResultadoAccion {
  exito: boolean
  mensaje: string
  datos?: Record<string, unknown>
  error?: string
}

// Conversaciones
export interface ConversacionBase {
  id: string
  session_id: string
  user_id?: string
  titulo?: string
  proyecto_activo_id?: number
  proyecto_nombre?: string
  vista_actual: string
  activa: boolean
  total_mensajes: number
  created_at: string
  updated_at: string
}

export interface Conversacion extends ConversacionBase {}

export interface ConversacionConMensajes extends ConversacionBase {
  mensajes: MensajeResponse[]
}

// Chat Request/Response
export interface ChatRequest {
  mensaje: string
  conversacion_id?: string
  session_id: string
  user_id?: string
  proyecto_contexto_id?: number
  vista_actual?: string
}

export interface ChatResponse {
  conversacion_id: string
  mensaje: MensajeResponse
  accion_pendiente?: AccionPendiente
  sugerencias: string[]
  contexto_actualizado: boolean
}

// Streaming
export interface ChatStreamChunk {
  tipo: 'texto' | 'tool_start' | 'tool_end' | 'done' | 'error'
  contenido?: string
  tool_call?: ToolCall
  tool_result?: Record<string, unknown>
  error?: string
}

// Notificaciones
export interface NotificacionProactiva {
  id: string
  trigger_codigo: string
  mensaje: string
  proyecto_id?: number
  proyecto_nombre?: string
  accion_sugerida?: string
  accion_parametros?: Record<string, unknown>
  created_at: string
}

// Feedback
export interface FeedbackCreate {
  mensaje_id: string
  valoracion?: number
  es_util?: boolean
  comentario?: string
  categorias_problema: string[]
}

export interface Feedback {
  id: string
  mensaje_id: string
  valoracion?: number
  es_util?: boolean
  comentario?: string
  created_at: string
}

// Herramientas
export interface HerramientaInfo {
  name: string
  description: string
  categoria: string
  requiere_confirmacion: boolean
  permisos_requeridos: string[]
}

export interface HerramientasDisponibles {
  herramientas: HerramientaInfo[]
  total: number
}

// WebSocket
export interface WebSocketMessage {
  tipo: 'chat' | 'notificacion' | 'accion' | 'typing' | 'ping' | 'pong' | 'error'
  payload?: Record<string, unknown>
}

export interface WebSocketTyping {
  is_typing: boolean
  mensaje_parcial?: string
}

// Estado del asistente
export interface EstadoAsistente {
  conectado: boolean
  escribiendo: boolean
  procesando: boolean
  error?: string
}

// Búsqueda Web (Perplexity)
export type ModoBusquedaWeb = 'chat' | 'research' | 'reasoning'

export interface BusquedaWebRequest {
  query: string
  modo?: ModoBusquedaWeb
  contexto_chile?: boolean
}

export interface FuenteWeb {
  titulo: string
  url: string
  fragmento?: string
}

export interface BusquedaWebResponse {
  respuesta: string
  fuentes: FuenteWeb[]
  proveedor: string
  modelo: string
  tokens_usados: number
  metadata: Record<string, unknown>
}

export interface RouterInfo {
  routing: Record<string, string>
  perplexity_habilitado: boolean
}
