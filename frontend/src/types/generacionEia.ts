/**
 * Tipos para Generación de EIA (Fase 4).
 */

// =============================================================================
// Enums
// =============================================================================

export type EstadoDocumentoEIA = 'borrador' | 'en_revision' | 'validado' | 'final'
export type FormatoExportacionEIA = 'pdf' | 'docx' | 'eseia_xml'
export type TipoValidacionEIA = 'contenido' | 'formato' | 'referencia' | 'completitud' | 'normativa'
export type SeveridadValidacion = 'error' | 'warning' | 'info'
export type EstadoObservacionEIA = 'pendiente' | 'corregida' | 'ignorada'
export type EstadoGeneracionEIA = 'pendiente' | 'generando' | 'completado' | 'error'

// =============================================================================
// Contenido de Capítulos
// =============================================================================

export interface ContenidoCapitulo {
  numero: number
  titulo: string
  contenido: string
  subsecciones: Record<string, unknown>
  figuras: string[]
  tablas: string[]
  referencias: string[]
}

export interface MetadatosDocumento {
  fecha_elaboracion?: string | null
  empresa_consultora?: string | null
  autores: string[]
  revisores: string[]
  version_doc?: string | null
  resumen_ejecutivo?: string | null
}

export interface EstadisticasDocumento {
  total_paginas: number
  total_palabras: number
  total_figuras: number
  total_tablas: number
  total_referencias: number
  capitulos_completados: number
  porcentaje_completitud: number
}

// =============================================================================
// Documento EIA
// =============================================================================

export interface DocumentoEIA {
  id: number
  proyecto_id: number
  titulo: string
  estado: EstadoDocumentoEIA
  version: number
  contenido_capitulos?: Record<string, ContenidoCapitulo> | null
  metadatos?: MetadatosDocumento | null
  validaciones?: Record<string, unknown> | null
  estadisticas?: EstadisticasDocumento | null
  created_at: string
  updated_at: string
}

export interface DocumentoEIAUpdate {
  titulo?: string
  estado?: EstadoDocumentoEIA
  contenido_capitulos?: Record<string, ContenidoCapitulo>
  metadatos?: MetadatosDocumento
}

// =============================================================================
// Versiones
// =============================================================================

export interface VersionEIA {
  id: number
  documento_id: number
  version: number
  cambios: string
  creado_por?: string | null
  created_at: string
}

export interface CrearVersionRequest {
  cambios: string
  creado_por?: string
}

// =============================================================================
// Generación
// =============================================================================

export interface CompilarDocumentoRequest {
  incluir_capitulos?: number[] | null
  regenerar_existentes: boolean
}

export interface GenerarCapituloRequest {
  capitulo_numero: number
  regenerar: boolean
  instrucciones_adicionales?: string | null
}

export interface RegenerarSeccionRequest {
  capitulo_numero: number
  seccion_codigo: string
  instrucciones: string
}

export interface ProgresoGeneracion {
  capitulo_numero: number
  titulo: string
  estado: EstadoGeneracionEIA
  progreso_porcentaje: number
  palabras_generadas: number
  tiempo_estimado_segundos?: number | null
  error?: string | null
}

export interface GeneracionResponse {
  documento_id: number
  capitulos_generados: number[]
  capitulos_con_error: number[]
  tiempo_total_segundos: number
  estadisticas: EstadisticasDocumento
}

// =============================================================================
// Validación
// =============================================================================

export interface ObservacionValidacion {
  id: number
  documento_id: number
  regla_id?: number | null
  capitulo_numero?: number | null
  seccion?: string | null
  tipo_observacion: string
  severidad: SeveridadValidacion
  mensaje: string
  sugerencia?: string | null
  contexto?: Record<string, unknown> | null
  estado: EstadoObservacionEIA
  created_at: string
  resuelta_at?: string | null
}

export interface ResultadoValidacion {
  documento_id: number
  total_observaciones: number
  observaciones_por_severidad: Record<string, number>
  observaciones_por_capitulo: Record<number, number>
  observaciones: ObservacionValidacion[]
  es_valido: boolean
  mensaje_resumen: string
}

export interface ValidacionRequest {
  incluir_capitulos?: number[] | null
  nivel_severidad_minima: SeveridadValidacion
}

// =============================================================================
// Exportación
// =============================================================================

export interface ConfiguracionPDF {
  incluir_portada: boolean
  incluir_indice: boolean
  incluir_figuras: boolean
  incluir_tablas: boolean
  tamano_pagina: string
  orientacion: 'portrait' | 'landscape'
  margen_cm: number
  fuente: string
  tamano_fuente: number
  logo_empresa?: string | null
}

export interface ConfiguracionDOCX {
  incluir_portada: boolean
  incluir_indice: boolean
  incluir_figuras: boolean
  incluir_tablas: boolean
  estilo_documento: string
  logo_empresa?: string | null
}

export interface ConfiguracionESEIA {
  incluir_anexos_digitales: boolean
  version_esquema: string
}

export interface ExportacionRequest {
  formato: FormatoExportacionEIA
  configuracion?: Record<string, unknown> | null
}

export interface ExportacionEIA {
  id: number
  documento_id: number
  formato: FormatoExportacionEIA
  archivo_path?: string | null
  tamano_bytes?: number | null
  generado_exitoso: boolean
  error_mensaje?: string | null
  created_at: string
  url_descarga?: string | null
}

// =============================================================================
// Documento Completo (con relaciones)
// =============================================================================

export interface DocumentoCompletoResponse {
  documento: DocumentoEIA
  versiones: VersionEIA[]
  exportaciones: ExportacionEIA[]
  observaciones_pendientes: ObservacionValidacion[]
  estadisticas: EstadisticasDocumento
  progreso_capitulos: ProgresoGeneracion[]
}

// =============================================================================
// Labels y constantes
// =============================================================================

export const ESTADO_DOCUMENTO_LABELS: Record<EstadoDocumentoEIA, string> = {
  borrador: 'Borrador',
  en_revision: 'En Revisión',
  validado: 'Validado',
  final: 'Final',
}

export const ESTADO_DOCUMENTO_COLORS: Record<EstadoDocumentoEIA, string> = {
  borrador: 'badge-ghost',
  en_revision: 'badge-warning',
  validado: 'badge-info',
  final: 'badge-success',
}

export const FORMATO_EXPORTACION_LABELS: Record<FormatoExportacionEIA, string> = {
  pdf: 'PDF',
  docx: 'Word (DOCX)',
  eseia_xml: 'e-SEIA (XML)',
}

export const FORMATO_EXPORTACION_ICONS: Record<FormatoExportacionEIA, string> = {
  pdf: 'heroicons:document-text',
  docx: 'heroicons:document',
  eseia_xml: 'heroicons:code-bracket',
}

export const SEVERIDAD_LABELS: Record<SeveridadValidacion, string> = {
  error: 'Error',
  warning: 'Advertencia',
  info: 'Información',
}

export const SEVERIDAD_COLORS: Record<SeveridadValidacion, string> = {
  error: 'badge-error',
  warning: 'badge-warning',
  info: 'badge-info',
}

export const SEVERIDAD_ICONS: Record<SeveridadValidacion, string> = {
  error: 'heroicons:x-circle',
  warning: 'heroicons:exclamation-triangle',
  info: 'heroicons:information-circle',
}

export const ESTADO_OBSERVACION_LABELS: Record<EstadoObservacionEIA, string> = {
  pendiente: 'Pendiente',
  corregida: 'Corregida',
  ignorada: 'Ignorada',
}

export const ESTADO_GENERACION_LABELS: Record<EstadoGeneracionEIA, string> = {
  pendiente: 'Pendiente',
  generando: 'Generando...',
  completado: 'Completado',
  error: 'Error',
}

export const ESTADO_GENERACION_COLORS: Record<EstadoGeneracionEIA, string> = {
  pendiente: 'badge-ghost',
  generando: 'badge-warning',
  completado: 'badge-success',
  error: 'badge-error',
}

// Títulos de los 11 capítulos del EIA
export const CAPITULOS_EIA: Record<number, string> = {
  1: 'Índice',
  2: 'Resumen Ejecutivo',
  3: 'Descripción del Proyecto',
  4: 'Plan de Cumplimiento de Legislación Ambiental',
  5: 'Permisos Ambientales Sectoriales',
  6: 'Línea de Base',
  7: 'Evaluación de Impacto Ambiental',
  8: 'Plan de Medidas de Mitigación, Reparación y Compensación',
  9: 'Plan de Prevención de Contingencias y Emergencias',
  10: 'Plan de Seguimiento Ambiental',
  11: 'Ficha Resumen del EIA',
}
