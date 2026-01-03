/**
 * Tipos TypeScript para Recopilacion Guiada (Fase 3).
 */

// =============================================================================
// ENUMS
// =============================================================================

export type EstadoSeccion = 'pendiente' | 'en_progreso' | 'completado' | 'validado'

export type TipoRespuesta =
  | 'texto'
  | 'numero'
  | 'fecha'
  | 'seleccion'
  | 'seleccion_multiple'
  | 'archivo'
  | 'coordenadas'
  | 'tabla'
  | 'booleano'

export type SeveridadInconsistencia = 'error' | 'warning' | 'info'

export type EstadoExtraccion = 'pendiente' | 'procesando' | 'completado' | 'error'

// =============================================================================
// CONSTANTES UI
// =============================================================================

export const ESTADO_SECCION_LABELS: Record<EstadoSeccion, string> = {
  pendiente: 'Pendiente',
  en_progreso: 'En Progreso',
  completado: 'Completado',
  validado: 'Validado',
}

export const ESTADO_SECCION_COLORS: Record<EstadoSeccion, string> = {
  pendiente: 'badge-ghost',
  en_progreso: 'badge-warning',
  completado: 'badge-success',
  validado: 'badge-info',
}

export const SEVERIDAD_COLORS: Record<SeveridadInconsistencia, string> = {
  error: 'alert-error',
  warning: 'alert-warning',
  info: 'alert-info',
}

// =============================================================================
// INTERFACES DE PREGUNTAS
// =============================================================================

export interface OpcionSeleccion {
  valor: string
  etiqueta: string
  descripcion?: string
}

export interface ValidacionPregunta {
  requerido?: boolean
  min?: number
  max?: number
  patron?: string
  mensaje_patron?: string
}

export interface PreguntaRecopilacion {
  id: number
  capitulo_numero: number
  seccion_codigo: string
  seccion_nombre?: string
  codigo_pregunta: string
  pregunta: string
  descripcion?: string
  tipo_respuesta: TipoRespuesta
  opciones?: OpcionSeleccion[]
  valor_por_defecto?: unknown
  validaciones?: ValidacionPregunta
  es_obligatoria: boolean
  condicion_activacion?: Record<string, unknown>
  orden: number
  activo?: boolean
}

export interface PreguntaConRespuesta extends PreguntaRecopilacion {
  respuesta_actual?: unknown
  es_valida: boolean
  mensaje_validacion?: string
}

// =============================================================================
// INTERFACES DE SECCIONES
// =============================================================================

export interface SeccionBase {
  capitulo_numero: number
  seccion_codigo: string
  seccion_nombre?: string
}

export interface SeccionConPreguntas extends SeccionBase {
  preguntas: PreguntaConRespuesta[]
  total_preguntas: number
  preguntas_obligatorias: number
  preguntas_respondidas: number
  progreso: number
  estado: EstadoSeccion
}

export interface SeccionResumen extends SeccionBase {
  estado: EstadoSeccion
  progreso: number
  tiene_inconsistencias: boolean
  documentos_vinculados: number
}

// =============================================================================
// INTERFACES DE CONTENIDO
// =============================================================================

export interface RespuestaIndividual {
  codigo_pregunta: string
  valor: unknown
}

export interface GuardarRespuestasRequest {
  respuestas: RespuestaIndividual[]
}

export interface ContenidoEIA {
  id: number
  proyecto_id: number
  capitulo_numero: number
  seccion_codigo: string
  seccion_nombre?: string
  contenido: Record<string, unknown>
  estado: EstadoSeccion
  progreso: number
  documentos_vinculados: number[]
  validaciones: Record<string, unknown>[]
  inconsistencias: Record<string, unknown>[]
  sugerencias: Record<string, unknown>[]
  notas?: string
  created_at?: string
  updated_at?: string
}

// =============================================================================
// INTERFACES DE CAPITULOS Y PROGRESO
// =============================================================================

export interface CapituloProgreso {
  numero: number
  titulo: string
  total_secciones: number
  secciones_completadas: number
  progreso: number
  estado: EstadoSeccion
  tiene_inconsistencias: boolean
  secciones: SeccionResumen[]
}

export interface ProgresoGeneralEIA {
  proyecto_id: number
  total_capitulos: number
  capitulos_completados: number
  progreso_general: number
  total_inconsistencias: number
  capitulos: CapituloProgreso[]
}

export interface IniciarCapituloResponse {
  capitulo_numero: number
  titulo: string
  secciones: SeccionConPreguntas[]
  total_preguntas: number
  preguntas_obligatorias: number
  mensaje_bienvenida: string
}

// =============================================================================
// INTERFACES DE INCONSISTENCIAS
// =============================================================================

export interface InconsistenciaDetectada {
  regla_codigo: string
  regla_nombre: string
  capitulo_origen: number
  seccion_origen: string
  campo_origen: string
  valor_origen?: unknown
  capitulo_destino: number
  seccion_destino: string
  campo_destino: string
  valor_destino?: unknown
  mensaje: string
  severidad: SeveridadInconsistencia
  fecha_deteccion?: string
}

export interface ValidacionConsistenciaResponse {
  proyecto_id: number
  total_reglas_evaluadas: number
  inconsistencias: InconsistenciaDetectada[]
  errores: number
  warnings: number
  es_consistente: boolean
}

// =============================================================================
// INTERFACES DE EXTRACCION
// =============================================================================

export interface MapeoSeccionSugerido {
  capitulo_numero: number
  seccion_codigo: string
  campo: string
  valor: unknown
  confianza: number
}

export interface ExtraccionDocumento {
  id: number
  proyecto_id: number
  documento_id: number
  tipo_documento?: string
  datos_extraidos: Record<string, unknown>
  mapeo_secciones: MapeoSeccionSugerido[]
  confianza_extraccion: number
  estado: EstadoExtraccion
  errores: Record<string, unknown>[]
  procesado_por: string
  created_at?: string
  updated_at?: string
}

export interface ExtraccionDocumentoRequest {
  documento_id: number
  tipo_documento?: string
  forzar_reprocesar?: boolean
}

// =============================================================================
// INTERFACES DE VINCULACION
// =============================================================================

export interface VincularDocumentoRequest {
  documento_id: number
  capitulo_numero: number
  seccion_codigo: string
}
