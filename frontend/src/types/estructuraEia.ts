/**
 * Tipos para Estructura EIA (Fase 2).
 */

// Importar EstadoPAS desde ficha.ts para evitar duplicación
import type { EstadoPAS } from './ficha'
export type { EstadoPAS }

// =============================================================================
// Enums
// =============================================================================

export type EstadoCapitulo = 'pendiente' | 'en_progreso' | 'completado'
export type EstadoAnexo = 'pendiente' | 'en_elaboracion' | 'completado'
export type NivelComplejidad = 'baja' | 'media' | 'alta' | 'muy_alta'
export type ObligatoriedadPAS = 'obligatorio' | 'frecuente' | 'caso_a_caso'

// =============================================================================
// Capitulos EIA
// =============================================================================

export interface CapituloConEstado {
  numero: number
  titulo: string
  descripcion?: string | null
  contenido_requerido: string[]
  es_obligatorio: boolean
  estado: EstadoCapitulo
  progreso_porcentaje: number
  secciones_completadas: number
  secciones_totales: number
  notas?: string | null
}

export interface ActualizarCapituloRequest {
  estado: EstadoCapitulo
  progreso_porcentaje?: number
  notas?: string
}

// =============================================================================
// PAS con Estado
// =============================================================================

export interface PASConEstado {
  articulo: number
  nombre: string
  organismo: string
  obligatoriedad: ObligatoriedadPAS
  estado: EstadoPAS
  condiciones?: Record<string, unknown> | null
  fecha_limite?: string | null
  notas?: string | null
  razon_aplicacion?: string | null
}

export interface ActualizarPASRequest {
  estado: EstadoPAS
  fecha_limite?: string
  notas?: string
}

// =============================================================================
// Anexos Requeridos
// =============================================================================

export interface AnexoRequerido {
  codigo: string
  nombre: string
  descripcion?: string | null
  profesional_responsable?: string | null
  obligatorio: boolean
  estado: EstadoAnexo
  condicion_activacion?: Record<string, unknown> | null
  razon_aplicacion?: string | null
}

export interface ActualizarAnexoRequest {
  estado: EstadoAnexo
  notas?: string
}

// =============================================================================
// Componentes de Linea Base
// =============================================================================

export interface ComponenteLineaBaseEnPlan {
  codigo: string
  nombre: string
  descripcion?: string | null
  metodologia?: string | null
  variables_monitorear: string[]
  estudios_requeridos: string[]
  duracion_estimada_dias: number
  es_obligatorio: boolean
  aplica: boolean
  razon_aplicacion?: string | null
  prioridad: number
}

// =============================================================================
// Estimacion de Complejidad
// =============================================================================

export interface FactorComplejidad {
  nombre: string
  descripcion: string
  peso: number
  valor: number
  contribucion: number
}

export interface RecursoSugerido {
  tipo: string
  nombre: string
  descripcion?: string | null
  cantidad: number
  prioridad: string
}

export interface EstimacionComplejidad {
  nivel: NivelComplejidad
  puntaje: number
  factores: FactorComplejidad[]
  tiempo_estimado_meses: number
  recursos_sugeridos: RecursoSugerido[]
  riesgos_principales: string[]
  recomendaciones: string[]
}

// =============================================================================
// Estructura EIA Completa
// =============================================================================

export interface EstructuraEIA {
  id: number
  proyecto_id: number
  version: number
  capitulos: CapituloConEstado[]
  pas_requeridos: PASConEstado[]
  anexos_requeridos: AnexoRequerido[]
  plan_linea_base: ComponenteLineaBaseEnPlan[]
  estimacion_complejidad?: EstimacionComplejidad | null
  progreso_general: number
  capitulos_completados: number
  total_capitulos: number
  pas_aprobados: number
  total_pas: number
  notas?: string | null
  created_at: string
  updated_at?: string | null
}

export interface EstructuraEIAResumen {
  id: number
  proyecto_id: number
  version: number
  progreso_general: number
  total_capitulos: number
  total_pas: number
  total_anexos: number
  nivel_complejidad?: NivelComplejidad | null
  created_at: string
}

// =============================================================================
// Requests
// =============================================================================

export interface GenerarEstructuraRequest {
  proyecto_id: number
  forzar_regenerar?: boolean
}

// =============================================================================
// Labels y constantes
// =============================================================================

export const ESTADO_CAPITULO_LABELS: Record<EstadoCapitulo, string> = {
  pendiente: 'Pendiente',
  en_progreso: 'En Progreso',
  completado: 'Completado',
}

// ESTADO_PAS_LABELS ya está definido en ficha.ts - usar ese

export const ESTADO_ANEXO_LABELS: Record<EstadoAnexo, string> = {
  pendiente: 'Pendiente',
  en_elaboracion: 'En Elaboracion',
  completado: 'Completado',
}

export const NIVEL_COMPLEJIDAD_LABELS: Record<NivelComplejidad, string> = {
  baja: 'Baja',
  media: 'Media',
  alta: 'Alta',
  muy_alta: 'Muy Alta',
}

export const NIVEL_COMPLEJIDAD_COLORS: Record<NivelComplejidad, string> = {
  baja: 'badge-success',
  media: 'badge-info',
  alta: 'badge-warning',
  muy_alta: 'badge-error',
}

export const ESTADO_CAPITULO_COLORS: Record<EstadoCapitulo, string> = {
  pendiente: 'badge-ghost',
  en_progreso: 'badge-warning',
  completado: 'badge-success',
}

export const ESTADO_PAS_COLORS: Record<EstadoPAS, string> = {
  identificado: 'badge-ghost',
  requerido: 'badge-warning',
  en_tramite: 'badge-info',
  aprobado: 'badge-success',
  no_aplica: 'badge-neutral',
  rechazado: 'badge-error',
}

export const ESTADO_ANEXO_COLORS: Record<EstadoAnexo, string> = {
  pendiente: 'badge-ghost',
  en_elaboracion: 'badge-warning',
  completado: 'badge-success',
}
