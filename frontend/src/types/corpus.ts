/**
 * Tipos para el sistema de gestión de corpus RAG.
 */

// ============================================================================
// CATEGORIAS
// ============================================================================

export interface Categoria {
  id: number
  codigo: string
  nombre: string
  descripcion: string | null
  tipo_documentos_permitidos: string[]
  icono: string | null
  color: string | null
  parent_id: number | null
  nivel: number
  orden: number
  activo: boolean
  cantidad_documentos: number
}

export interface CategoriaConHijos extends Categoria {
  hijos: CategoriaConHijos[]
}

// ============================================================================
// TEMAS
// ============================================================================

export type GrupoTema = 'componente_ambiental' | 'trigger_art11' | 'etapa_seia' | 'sector' | 'otro'

export interface Tema {
  id: number
  codigo: string
  nombre: string
  descripcion: string | null
  grupo: GrupoTema
  keywords: string[]
  color: string | null
  icono: string | null
  activo: boolean
  cantidad_fragmentos: number
}

// ============================================================================
// COLECCIONES
// ============================================================================

export interface Coleccion {
  id: number
  codigo: string
  nombre: string
  descripcion: string | null
  es_publica: boolean
  color: string | null
  icono: string | null
  orden: number
  cantidad_documentos: number
}

// ============================================================================
// DOCUMENTOS
// ============================================================================

export type EstadoDocumento = 'vigente' | 'derogado' | 'modificado' | 'borrador'

export interface DocumentoResumen {
  id: number
  titulo: string
  tipo: string
  numero: string | null
  fecha_publicacion: string | null
  estado: EstadoDocumento
  categoria_id: number | null
  categoria_nombre: string | null
  tiene_archivo: boolean
  fragmentos_count: number
  created_at: string
}

export interface DocumentoDetalle extends DocumentoResumen {
  fecha_vigencia: string | null
  fecha_vigencia_fin: string | null
  organismo: string | null
  url_fuente: string | null
  resolucion_aprobatoria: string | null
  sectores: string[]
  tipologias_art3: string[]
  triggers_art11: string[]
  componentes_ambientales: string[]
  regiones_aplicables: string[]
  etapa_proceso: string | null
  actor_principal: string | null
  resumen: string | null
  palabras_clave: string[]
  // Contenido del documento
  contenido_completo: string | null
  contenido_chars: number
  // Archivo original
  archivo_nombre: string | null
  archivo_tipo: string | null
  archivo_tamano_mb: number | null
  colecciones: ColeccionResumen[]
  documentos_relacionados: DocumentoRelacionado[]
  version: number
  updated_at: string | null
}

export interface DocumentoRelacionado {
  id: number
  titulo: string
  tipo: string
  relacion: string
}

export interface ColeccionResumen {
  id: number
  codigo: string
  nombre: string
}

// ============================================================================
// FRAGMENTOS
// ============================================================================

export interface Fragmento {
  id: number
  seccion: string | null
  contenido: string
  contenido_truncado: boolean
  temas: string[]
  tiene_embedding: boolean
}

export interface FragmentosResponse {
  documento_id: number
  documento_titulo: string
  total: number
  limite: number
  offset: number
  fragmentos: Fragmento[]
}

// ============================================================================
// REQUESTS
// ============================================================================

export interface DocumentoCreateData {
  titulo: string
  tipo: string
  numero?: string
  fecha_publicacion?: string
  fecha_vigencia?: string
  organismo?: string
  url_fuente?: string
  resolucion_aprobatoria?: string
  categoria_id: number
  coleccion_ids?: number[]
  sectores?: string[]
  tipologias_art3?: string[]
  triggers_art11?: string[]
  componentes_ambientales?: string[]
  regiones_aplicables?: string[]
  etapa_proceso?: string
  actor_principal?: string
  contenido?: string
  resumen?: string
  palabras_clave?: string[]
}

export interface DocumentoUpdateData {
  titulo?: string
  tipo?: string
  numero?: string
  fecha_publicacion?: string
  fecha_vigencia?: string
  organismo?: string
  url_fuente?: string
  resolucion_aprobatoria?: string
  estado?: EstadoDocumento
  categoria_id?: number
  coleccion_ids?: number[]
  sectores?: string[]
  tipologias_art3?: string[]
  triggers_art11?: string[]
  componentes_ambientales?: string[]
  regiones_aplicables?: string[]
  etapa_proceso?: string
  actor_principal?: string
  resumen?: string
  palabras_clave?: string[]
}

export interface DocumentoFiltros {
  categoria_id?: number
  tipo?: string
  estado?: EstadoDocumento
  sector?: string
  trigger_art11?: string
  componente?: string
  coleccion_id?: number
  etapa_proceso?: string
  actor_principal?: string
  q?: string
  limite?: number
  offset?: number
  orden?: 'fecha_desc' | 'fecha_asc' | 'titulo_asc' | 'titulo_desc'
}

// ============================================================================
// RESPONSES
// ============================================================================

export interface ListaDocumentosResponse {
  total: number
  limite: number
  offset: number
  documentos: DocumentoResumen[]
}

export interface TipoDocumentoStats {
  tipo: string
  cantidad: number
}

export interface TiposDocumentoResponse {
  tipos: TipoDocumentoStats[]
  total_tipos: number
}

export interface ReprocesarResponse {
  mensaje: string
  documento_id: number
  fragmentos_creados: number
  temas_detectados: string[]
}

export interface RelacionResponse {
  mensaje: string
  id: number
  origen: { id: number; titulo: string }
  destino: { id: number; titulo: string }
  tipo: string
}

// ============================================================================
// CONSTANTES
// ============================================================================

export const TIPOS_DOCUMENTO = [
  { value: 'Ley', label: 'Ley' },
  { value: 'Reglamento', label: 'Reglamento' },
  { value: 'Decreto', label: 'Decreto' },
  { value: 'Guia SEA', label: 'Guia SEA' },
  { value: 'Criterio', label: 'Criterio de Evaluacion' },
  { value: 'Instructivo', label: 'Instructivo' },
  { value: 'Ordinario', label: 'Ordinario' },
  { value: 'Jurisprudencia', label: 'Jurisprudencia' },
  { value: 'Otro', label: 'Otro' },
] as const

export const ESTADOS_DOCUMENTO = [
  { value: 'vigente', label: 'Vigente', color: 'success' },
  { value: 'derogado', label: 'Derogado', color: 'error' },
  { value: 'modificado', label: 'Modificado', color: 'warning' },
  { value: 'borrador', label: 'Borrador', color: 'info' },
] as const

export const GRUPOS_TEMA: Record<GrupoTema, { label: string; color: string }> = {
  componente_ambiental: { label: 'Componente Ambiental', color: 'info' },
  trigger_art11: { label: 'Trigger Art. 11', color: 'error' },
  etapa_seia: { label: 'Etapa SEIA', color: 'warning' },
  sector: { label: 'Sector', color: 'success' },
  otro: { label: 'Otro', color: 'neutral' },
}

export const TIPOS_RELACION = [
  { value: 'reglamenta', label: 'Reglamenta' },
  { value: 'interpreta', label: 'Interpreta' },
  { value: 'reemplaza', label: 'Reemplaza' },
  { value: 'complementa', label: 'Complementa' },
  { value: 'cita', label: 'Cita' },
  { value: 'modifica', label: 'Modifica' },
] as const
