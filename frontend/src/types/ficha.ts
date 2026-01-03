/**
 * Tipos para Ficha Acumulativa del Proyecto.
 */

// Categorias de caracteristicas
export type CategoriaCaracteristica =
  | 'identificacion'
  | 'tecnico'
  | 'obras'
  | 'fases'
  | 'insumos'
  | 'emisiones'
  | 'social'
  | 'ambiental'

// Fuente de datos
export type FuenteDato = 'manual' | 'asistente' | 'documento' | 'gis'

// Estado de PAS
export type EstadoPAS =
  | 'identificado'
  | 'requerido'
  | 'no_aplica'
  | 'en_tramite'
  | 'aprobado'
  | 'rechazado'

// Estado de literal Art. 11
export type EstadoLiteralArt11 = 'pendiente' | 'no_aplica' | 'probable' | 'confirmado'

// Via sugerida
export type ViaSugerida = 'DIA' | 'EIA' | 'NO_SEIA' | 'INDEFINIDO'

// Caracteristica del proyecto
export interface Caracteristica {
  id: number
  proyecto_id: number
  categoria: CategoriaCaracteristica
  clave: string
  valor: string | null
  valor_numerico: number | null
  unidad: string | null
  fuente: FuenteDato
  pregunta_codigo: string | null
  notas: string | null
  validado: boolean
  validado_por: string | null
  validado_fecha: string | null
  created_at: string
  updated_at: string
}

// Crear caracteristica
export interface CaracteristicaCreate {
  categoria: CategoriaCaracteristica
  clave: string
  valor?: string
  valor_numerico?: number
  unidad?: string
  fuente?: FuenteDato
  pregunta_codigo?: string
  notas?: string
}

// Actualizar caracteristica
export interface CaracteristicaUpdate {
  valor?: string
  valor_numerico?: number
  unidad?: string
  fuente?: FuenteDato
  notas?: string
  validado?: boolean
}

// Caracteristicas agrupadas por categoria
export interface CaracteristicasPorCategoria {
  identificacion: Record<string, unknown>
  tecnico: Record<string, unknown>
  obras: Record<string, unknown>
  fases: Record<string, unknown>
  insumos: Record<string, unknown>
  emisiones: Record<string, unknown>
  social: Record<string, unknown>
  ambiental: Record<string, unknown>
}

// Ubicacion del proyecto
export interface UbicacionProyecto {
  id: number
  proyecto_id: number
  regiones: string[] | null
  provincias: string[] | null
  comunas: string[] | null
  alcance: string | null
  superficie_ha: number | null
  version: number
  es_vigente: boolean
  fuente: string
  analisis_gis_cache: Record<string, unknown> | null
  analisis_gis_fecha: string | null
  created_at: string
}

// PAS del proyecto
export interface PASProyecto {
  id: number
  proyecto_id: number
  articulo: number
  nombre: string
  organismo: string
  estado: EstadoPAS
  obligatorio: boolean
  justificacion: string | null
  condicion_activada: Record<string, unknown> | null
  identificado_por: string
  created_at: string
  updated_at: string
}

// Crear PAS
export interface PASProyectoCreate {
  articulo: number
  nombre: string
  organismo: string
  estado?: EstadoPAS
  obligatorio?: boolean
  justificacion?: string
  condicion_activada?: Record<string, unknown>
}

// Actualizar PAS
export interface PASProyectoUpdate {
  estado?: EstadoPAS
  obligatorio?: boolean
  justificacion?: string
  numero_resolucion?: string
}

// Analisis de literal Art. 11
export interface AnalisisArt11 {
  id: number
  proyecto_id: number
  literal: string
  estado: EstadoLiteralArt11
  justificacion: string | null
  confianza: number | null
  evidencias: Record<string, unknown>[]
  fuente_gis: boolean
  fuente_usuario: boolean
  fuente_asistente: boolean
  created_at: string
  updated_at: string
}

// Crear analisis Art. 11
export interface AnalisisArt11Create {
  literal: string
  estado?: EstadoLiteralArt11
  justificacion?: string
  confianza?: number
  evidencias?: Record<string, unknown>[]
  fuente_gis?: boolean
  fuente_usuario?: boolean
  fuente_asistente?: boolean
}

// Diagnostico del proyecto
export interface Diagnostico {
  id: number
  proyecto_id: number
  version: number
  via_sugerida: ViaSugerida | null
  confianza: number | null
  resumen: string | null
  literales_gatillados: string[]
  cumple_umbral_seia: boolean | null
  umbral_evaluado: Record<string, unknown> | null
  permisos_identificados: Record<string, unknown>[]
  alertas: Record<string, unknown>[]
  recomendaciones: Record<string, unknown>[]
  generado_por: string
  created_at: string
}

// Ficha completa del proyecto
export interface FichaProyecto {
  proyecto_id: number
  nombre: string
  estado: string
  tipo_codigo: string | null
  tipo_nombre: string | null
  subtipo_codigo: string | null
  subtipo_nombre: string | null
  ubicacion: UbicacionProyecto | null
  caracteristicas: CaracteristicasPorCategoria
  analisis_art11: Record<string, AnalisisArt11>
  diagnostico_actual: Diagnostico | null
  pas: PASProyecto[]
  total_caracteristicas: number
  caracteristicas_validadas: number
  progreso_porcentaje: number
  created_at: string | null
  updated_at: string | null
}

// Resumen de ficha
export interface FichaResumen {
  proyecto_id: number
  nombre: string
  estado: string
  tipo_nombre: string | null
  via_sugerida: string | null
  progreso_porcentaje: number
  total_pas: number
  has_ubicacion: boolean
}

// Progreso de la ficha
export interface ProgresoFicha {
  proyecto_id: number
  total_campos: number
  campos_completados: number
  campos_validados: number
  porcentaje_completitud: number
  porcentaje_validacion: number
  por_categoria: Record<string, { total: number; validadas: number }>
  campos_faltantes_obligatorios: string[]
}

// Guardar respuesta del asistente
export interface GuardarRespuestaAsistente {
  categoria: CategoriaCaracteristica
  clave: string
  valor?: string
  valor_numerico?: number
  unidad?: string
  pregunta_codigo?: string
}

// Response de guardar respuestas
export interface GuardarRespuestasResponse {
  guardadas: number
  actualizadas: number
  errores: { clave: string; error: string }[]
  caracteristicas: Caracteristica[]
}

// Labels para categorias
export const CATEGORIA_LABELS: Record<CategoriaCaracteristica, string> = {
  identificacion: 'Identificacion',
  tecnico: 'Parametros Tecnicos',
  obras: 'Obras y Partes',
  fases: 'Cronograma y Fases',
  insumos: 'Insumos',
  emisiones: 'Emisiones y Residuos',
  social: 'Aspectos Sociales',
  ambiental: 'Aspectos Ambientales',
}

// Labels para estados PAS
export const ESTADO_PAS_LABELS: Record<EstadoPAS, string> = {
  identificado: 'Identificado',
  requerido: 'Requerido',
  no_aplica: 'No Aplica',
  en_tramite: 'En Tramite',
  aprobado: 'Aprobado',
  rechazado: 'Rechazado',
}

// Labels para estados literal Art. 11
export const ESTADO_ART11_LABELS: Record<EstadoLiteralArt11, string> = {
  pendiente: 'Pendiente',
  no_aplica: 'No Aplica',
  probable: 'Probable',
  confirmado: 'Confirmado',
}

// Labels para via sugerida
export const VIA_SUGERIDA_LABELS: Record<ViaSugerida, string> = {
  DIA: 'DIA',
  EIA: 'EIA',
  NO_SEIA: 'No Ingresa al SEIA',
  INDEFINIDO: 'Indefinido',
}
