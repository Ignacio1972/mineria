/**
 * Tipos para Componentes EIA Checklist y Workflow de Progreso.
 */

// Fases del workflow EIA
export type FaseProyecto =
  | 'identificacion'
  | 'prefactibilidad'
  | 'recopilacion'
  | 'generacion'
  | 'refinamiento'

// Estados de un componente del checklist
export type EstadoComponente = 'pendiente' | 'en_progreso' | 'completado'

// Prioridades
export type Prioridad = 'alta' | 'media' | 'baja'

// Material RAG asociado a un componente
export interface MaterialRAG {
  documento_id: number
  titulo: string
  contenido: string
  similitud: number
}

// Componente del checklist EIA
export interface ComponenteChecklist {
  id: number
  proyecto_id: number
  analisis_id: number | null
  componente: string
  capitulo: number
  nombre: string
  descripcion: string | null
  requerido: boolean
  prioridad: Prioridad
  estado: EstadoComponente
  progreso_porcentaje: number
  material_rag: MaterialRAG[]
  sugerencias_busqueda: string[]
  razon_inclusion: string | null
  triggers_relacionados: string[]
  created_at: string
  updated_at: string
}

// Para actualizar un componente
export interface ComponenteChecklistUpdate {
  estado?: EstadoComponente
  progreso_porcentaje?: number
}

// Información de una fase del workflow
export interface FaseInfo {
  id: FaseProyecto
  nombre: string
  descripcion: string
  rango_progreso: [number, number]
  completada: boolean
  activa: boolean
}

// Estadísticas de componentes
export interface EstadisticasComponentes {
  total: number
  completados: number
  en_progreso: number
  pendientes: number
}

// Respuesta del endpoint de progreso
export interface ProgresoProyecto {
  proyecto_id: number
  fase_actual: FaseProyecto
  progreso_global: number
  fases: FaseInfo[]
  componentes_checklist: EstadisticasComponentes
}

// Constantes para las fases
export const FASES_WORKFLOW: { id: FaseProyecto; nombre: string; icono: string; color: string }[] = [
  { id: 'identificacion', nombre: 'Identificacion', icono: 'map-pin', color: 'primary' },
  { id: 'prefactibilidad', nombre: 'Prefactibilidad', icono: 'clipboard-check', color: 'secondary' },
  { id: 'recopilacion', nombre: 'Recopilacion', icono: 'folder-open', color: 'accent' },
  { id: 'generacion', nombre: 'Generacion', icono: 'document-text', color: 'info' },
  { id: 'refinamiento', nombre: 'Refinamiento', icono: 'check-circle', color: 'success' },
]

// Nombres de los capítulos del checklist (diferentes a los capítulos del documento EIA)
export const CAPITULOS_CHECKLIST: Record<number, string> = {
  1: 'Descripcion del Proyecto',
  2: 'Area de Influencia',
  3: 'Linea de Base',
  4: 'Prediccion y Evaluacion de Impactos',
  5: 'Plan de Medidas de Mitigacion',
  6: 'Plan de Prevencion de Contingencias',
  7: 'Plan de Seguimiento Ambiental',
  8: 'Participacion Ciudadana',
  9: 'Plan de Cumplimiento y PAS',
  10: 'Compromisos Voluntarios',
  11: 'Fichas Resumen',
}

// Colores para estados
export const COLORES_ESTADO: Record<EstadoComponente, string> = {
  pendiente: 'badge-ghost',
  en_progreso: 'badge-warning',
  completado: 'badge-success',
}

// Colores para prioridad
export const COLORES_PRIORIDAD: Record<Prioridad, string> = {
  alta: 'badge-error',
  media: 'badge-warning',
  baja: 'badge-info',
}
