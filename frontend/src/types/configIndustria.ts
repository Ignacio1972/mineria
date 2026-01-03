/**
 * Tipos para Configuracion por Industria.
 */

// Tipo de proyecto (industria)
export interface TipoProyecto {
  id: number
  codigo: string
  nombre: string
  letra_art3: string | null
  descripcion: string | null
  activo: boolean
  created_at: string
}

export interface TipoProyectoConSubtipos extends TipoProyecto {
  subtipos: SubtipoProyecto[]
}

// Subtipo de proyecto
export interface SubtipoProyecto {
  id: number
  tipo_proyecto_id: number
  codigo: string
  nombre: string
  descripcion: string | null
  activo: boolean
}

// Umbral SEIA
export interface UmbralSEIA {
  id: number
  tipo_proyecto_id: number
  subtipo_id: number | null
  parametro: string
  operador: string
  valor: number
  unidad: string | null
  resultado: 'ingresa_seia' | 'no_ingresa' | 'requiere_eia'
  descripcion: string | null
  norma_referencia: string | null
  activo: boolean
}

// PAS por tipo
export interface PASPorTipo {
  id: number
  tipo_proyecto_id: number
  subtipo_id: number | null
  articulo: number
  nombre: string
  organismo: string
  obligatoriedad: 'obligatorio' | 'frecuente' | 'caso_a_caso'
  condicion_activacion: Record<string, unknown> | null
  descripcion: string | null
  activo: boolean
}

export interface PASAplicable {
  pas: PASPorTipo
  aplica: boolean
  razon: string
}

// Normativa por tipo
export interface NormativaPorTipo {
  id: number
  tipo_proyecto_id: number
  norma: string
  nombre: string
  componente: string | null
  tipo_norma: 'calidad' | 'emision' | 'sectorial' | null
  aplica_siempre: boolean
  descripcion: string | null
  activo: boolean
}

// OAECA por tipo
export interface OAECAPorTipo {
  id: number
  tipo_proyecto_id: number
  organismo: string
  competencias: string[]
  relevancia: 'principal' | 'secundario'
  activo: boolean
}

// Impacto por tipo
export interface ImpactoPorTipo {
  id: number
  tipo_proyecto_id: number
  subtipo_id: number | null
  componente: string
  impacto: string
  fase: 'construccion' | 'operacion' | 'cierre' | null
  frecuencia: 'muy_comun' | 'frecuente' | 'ocasional' | null
  activo: boolean
}

// Anexo por tipo
export interface AnexoPorTipo {
  id: number
  tipo_proyecto_id: number
  subtipo_id: number | null
  codigo: string
  nombre: string
  profesional_responsable: string | null
  obligatorio: boolean
  condicion_activacion: Record<string, unknown> | null
  activo: boolean
}

// Pregunta del arbol
export interface ArbolPregunta {
  id: number
  tipo_proyecto_id: number
  subtipo_id: number | null
  codigo: string
  pregunta_texto: string
  tipo_respuesta: 'texto' | 'numero' | 'opcion' | 'archivo' | 'ubicacion' | 'boolean'
  opciones: { valor: string; texto: string }[] | null
  orden: number
  es_obligatoria: boolean
  campo_destino: string | null
  condicion_activacion: Record<string, unknown> | null
  valida_umbral: boolean
  activo: boolean
}

// Configuracion completa de industria
export interface ConfigIndustriaCompleta {
  tipo: TipoProyecto
  subtipo: SubtipoProyecto | null
  subtipos_disponibles: SubtipoProyecto[]
  umbrales: UmbralSEIA[]
  pas: PASPorTipo[]
  normativa: NormativaPorTipo[]
  oaeca: OAECAPorTipo[]
  impactos: ImpactoPorTipo[]
  anexos: AnexoPorTipo[]
  preguntas: ArbolPregunta[]
}

// Resumen de configuracion
export interface ConfigIndustriaResumen {
  tipo: TipoProyecto
  num_subtipos: number
  num_umbrales: number
  num_pas: number
  num_normativas: number
  num_preguntas: number
}

// Request para evaluar umbral
export interface EvaluarUmbralRequest {
  tipo_proyecto_codigo: string
  parametros: Record<string, number>
  subtipo_codigo?: string
}

// Response de evaluacion de umbral
export interface EvaluarUmbralResponse {
  cumple_umbral: boolean
  resultado: 'ingresa_seia' | 'no_ingresa' | 'requiere_eia'
  umbral_evaluado: UmbralSEIA | null
  valor_proyecto: number
  diferencia: number
  mensaje: string
}

// Responses de listas
export interface TiposProyectoListResponse {
  tipos: TipoProyectoConSubtipos[]
  total: number
}

export interface PASListResponse {
  pas: PASPorTipo[]
  total: number
}

export interface NormativaListResponse {
  normativas: NormativaPorTipo[]
  total: number
}

export interface PreguntasListResponse {
  preguntas: ArbolPregunta[]
  total: number
}

// Progreso de preguntas
export interface ProgresoPreguntas {
  preguntas_respondidas: number
  preguntas_totales: number
  porcentaje: number
  completado: boolean
}
