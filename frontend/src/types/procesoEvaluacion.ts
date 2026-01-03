/**
 * Tipos para Gestor de Proceso de Evaluacion SEIA (ICSARA/Adendas).
 */

// =============================================================================
// Enums
// =============================================================================

export type EstadoEvaluacion =
  | 'no_ingresado'
  | 'ingresado'
  | 'en_admisibilidad'
  | 'admitido'
  | 'inadmitido'
  | 'en_evaluacion'
  | 'icsara_emitido'
  | 'adenda_en_revision'
  | 'ice_emitido'
  | 'en_comision'
  | 'rca_aprobada'
  | 'rca_rechazada'
  | 'desistido'
  | 'caducado'

export type ResultadoRCA =
  | 'favorable'
  | 'favorable_con_condiciones'
  | 'desfavorable'
  | 'desistimiento'
  | 'caducidad'

export type EstadoICSARA =
  | 'emitido'
  | 'respondido'
  | 'parcialmente_respondido'
  | 'vencido'

export type EstadoAdenda =
  | 'en_elaboracion'
  | 'presentada'
  | 'en_revision'
  | 'aceptada'
  | 'con_observaciones'
  | 'rechazada'

export type ResultadoRevision =
  | 'suficiente'
  | 'insuficiente'
  | 'parcialmente_suficiente'

export type TipoObservacion = 'ampliacion' | 'aclaracion' | 'rectificacion'
export type PrioridadObservacion = 'critica' | 'importante' | 'menor'
export type EstadoObservacionICSARA = 'pendiente' | 'respondida' | 'parcial'
export type EstadoPlazo = 'normal' | 'alerta' | 'critico' | 'vencido'
export type EstadoTimeline = 'completado' | 'actual' | 'pendiente'

// =============================================================================
// Observaciones ICSARA
// =============================================================================

export interface ObservacionICSARA {
  id: string
  oaeca: string
  capitulo_eia: number
  componente?: string | null
  tipo: TipoObservacion
  texto: string
  prioridad: PrioridadObservacion
  estado: EstadoObservacionICSARA
}

export interface ObservacionICSARACreate {
  oaeca: string
  capitulo_eia: number
  componente?: string
  tipo: TipoObservacion
  texto: string
  prioridad: PrioridadObservacion
}

// =============================================================================
// Respuestas Adenda
// =============================================================================

export interface RespuestaAdenda {
  observacion_id: string
  respuesta: string
  anexos_referenciados: string[]
  estado: 'respondida' | 'parcial' | 'no_respondida'
  calificacion_sea?: 'suficiente' | 'insuficiente' | null
}

export interface RespuestaAdendaCreate {
  observacion_id: string
  respuesta: string
  anexos_referenciados?: string[]
  estado?: 'respondida' | 'parcial' | 'no_respondida'
}

// =============================================================================
// Condiciones RCA
// =============================================================================

export interface CondicionRCA {
  numero: number
  descripcion: string
  plazo?: string | null
  responsable?: string | null
}

// =============================================================================
// Adenda
// =============================================================================

export interface Adenda {
  id: number
  icsara_id: number
  numero_adenda: number
  fecha_presentacion: string
  respuestas: RespuestaAdenda[]
  total_respuestas: number
  observaciones_resueltas: number
  observaciones_pendientes: number
  porcentaje_resueltas: number
  estado: EstadoAdenda
  fecha_revision?: string | null
  resultado_revision?: ResultadoRevision | null
  archivo_id?: number | null
  created_at?: string | null
}

export interface AdendaCreate {
  numero_adenda: number
  fecha_presentacion: string
  respuestas?: RespuestaAdendaCreate[]
}

// =============================================================================
// ICSARA
// =============================================================================

export interface ICSARA {
  id: number
  proceso_evaluacion_id: number
  numero_icsara: number
  fecha_emision: string
  fecha_limite_respuesta: string
  dias_para_responder: number
  esta_vencido: boolean
  observaciones: ObservacionICSARA[]
  total_observaciones: number
  observaciones_resueltas: number
  observaciones_pendientes: number
  observaciones_por_oaeca: Record<string, number>
  estado: EstadoICSARA
  archivo_id?: number | null
  adendas: Adenda[]
  created_at?: string | null
}

export interface ICSARACreate {
  numero_icsara: number
  fecha_emision: string
  fecha_limite_respuesta: string
  observaciones?: ObservacionICSARACreate[]
}

// =============================================================================
// Proceso de Evaluacion
// =============================================================================

export interface ProcesoEvaluacion {
  id: number
  proyecto_id: number
  estado_evaluacion: EstadoEvaluacion
  fecha_ingreso?: string | null
  fecha_admisibilidad?: string | null
  fecha_rca?: string | null
  resultado_rca?: ResultadoRCA | null
  plazo_legal_dias: number
  dias_transcurridos: number
  dias_suspension: number
  dias_restantes: number
  porcentaje_plazo: number
  numero_rca?: string | null
  url_rca?: string | null
  condiciones_rca?: CondicionRCA[] | null
  total_icsara: number
  total_observaciones: number
  observaciones_pendientes: number
  icsaras: ICSARA[]
  created_at?: string | null
  updated_at?: string | null
}

// =============================================================================
// Resumen Proceso
// =============================================================================

export interface ResumenProcesoEvaluacion {
  proyecto_id: number
  proyecto_nombre?: string | null
  estado_actual: EstadoEvaluacion
  estado_label: string
  fecha_ingreso?: string | null
  dias_transcurridos: number
  dias_restantes: number
  porcentaje_plazo: number
  total_icsara: number
  icsara_actual?: number | null
  observaciones_totales: number
  observaciones_pendientes: number
  observaciones_resueltas: number
  observaciones_por_oaeca: Record<string, number>
  oaeca_criticos: string[]
  total_adendas: number
  ultima_adenda_fecha?: string | null
  proxima_accion: string
  fecha_limite?: string | null
  alerta?: string | null
}

// =============================================================================
// Plazos
// =============================================================================

export interface PlazoEvaluacion {
  plazo_legal_dias: number
  dias_transcurridos: number
  dias_suspension: number
  dias_efectivos: number
  dias_restantes: number
  porcentaje_transcurrido: number
  estado_plazo: EstadoPlazo
  fecha_limite_estimada?: string | null
}

// =============================================================================
// Timeline
// =============================================================================

export interface EstadoTimelineItem {
  id: string
  nombre: string
  descripcion: string
  estado: EstadoTimeline
  fecha?: string | null
  icono?: string | null
}

export interface TimelineEvaluacion {
  proyecto_id: number
  estados: EstadoTimelineItem[]
  estado_actual: EstadoEvaluacion
  progreso_porcentaje: number
}

// =============================================================================
// Estadisticas
// =============================================================================

export interface EstadisticasICSARA {
  total_observaciones: number
  por_tipo: Record<string, number>
  por_prioridad: Record<string, number>
  por_oaeca: Record<string, number>
  por_capitulo: Record<number, number>
  por_estado: Record<string, number>
  oaeca_mas_observaciones: string
  capitulo_mas_observaciones: number
}

// =============================================================================
// Requests
// =============================================================================

export interface IniciarProcesoRequest {
  fecha_ingreso: string
  instrumento: 'EIA' | 'DIA'
}

export interface RegistrarAdmisibilidadRequest {
  resultado: 'admitido' | 'inadmitido'
  fecha: string
  observaciones?: string
}

export interface RegistrarRCARequest {
  resultado: ResultadoRCA
  numero_rca: string
  fecha: string
  condiciones?: CondicionRCA[]
  url?: string
}

export interface ActualizarEstadoObservacionRequest {
  estado: EstadoObservacionICSARA
  calificacion?: 'suficiente' | 'insuficiente'
}

// =============================================================================
// OAECA (Organismos con Competencia Ambiental)
// =============================================================================

export interface OAECAInfo {
  nombre_completo: string
  competencias: string[]
}

export const OAECAS_MINERIA: Record<string, OAECAInfo> = {
  SERNAGEOMIN: {
    nombre_completo: 'Servicio Nacional de Geologia y Mineria',
    competencias: ['Geologia', 'Relaves', 'Botaderos', 'Plan de cierre minero'],
  },
  DGA: {
    nombre_completo: 'Direccion General de Aguas',
    competencias: ['Recursos hidricos', 'Derechos de agua', 'Hidrogeologia'],
  },
  SAG: {
    nombre_completo: 'Servicio Agricola y Ganadero',
    competencias: ['Flora', 'Fauna', 'Suelos agricolas', 'Subdivision predios'],
  },
  CONAF: {
    nombre_completo: 'Corporacion Nacional Forestal',
    competencias: ['Bosques', 'Areas silvestres protegidas', 'Flora nativa'],
  },
  'SEREMI Salud': {
    nombre_completo: 'Secretaria Regional Ministerial de Salud',
    competencias: ['Residuos', 'Aguas servidas', 'Ruido', 'Calidad del aire'],
  },
  'SEREMI MMA': {
    nombre_completo: 'Secretaria Regional Ministerial del Medio Ambiente',
    competencias: ['Coordinacion', 'Biodiversidad', 'Areas protegidas'],
  },
  CMN: {
    nombre_completo: 'Consejo de Monumentos Nacionales',
    competencias: ['Patrimonio arqueologico', 'Patrimonio historico'],
  },
  CONADI: {
    nombre_completo: 'Corporacion Nacional de Desarrollo Indigena',
    competencias: ['Pueblos indigenas', 'Tierras indigenas', 'CPLI'],
  },
  Municipalidad: {
    nombre_completo: 'Municipalidad respectiva',
    competencias: ['Uso de suelo', 'Planificacion territorial'],
  },
  SERNATUR: {
    nombre_completo: 'Servicio Nacional de Turismo',
    competencias: ['Turismo', 'ZOIT (Zonas de Interes Turistico)'],
  },
}

// =============================================================================
// Helpers
// =============================================================================

export const ESTADO_EVALUACION_LABELS: Record<EstadoEvaluacion, string> = {
  no_ingresado: 'No ingresado',
  ingresado: 'Ingresado',
  en_admisibilidad: 'En admisibilidad',
  admitido: 'Admitido',
  inadmitido: 'Inadmitido',
  en_evaluacion: 'En evaluacion',
  icsara_emitido: 'ICSARA emitido',
  adenda_en_revision: 'Adenda en revision',
  ice_emitido: 'ICE emitido',
  en_comision: 'En comision',
  rca_aprobada: 'RCA aprobada',
  rca_rechazada: 'RCA rechazada',
  desistido: 'Desistido',
  caducado: 'Caducado',
}

export const ESTADO_PLAZO_COLORS: Record<EstadoPlazo, string> = {
  normal: 'success',
  alerta: 'warning',
  critico: 'error',
  vencido: 'error',
}

export const PRIORIDAD_COLORS: Record<PrioridadObservacion, string> = {
  critica: 'error',
  importante: 'warning',
  menor: 'info',
}

export const TIPO_OBSERVACION_LABELS: Record<TipoObservacion, string> = {
  ampliacion: 'Ampliacion',
  aclaracion: 'Aclaracion',
  rectificacion: 'Rectificacion',
}
