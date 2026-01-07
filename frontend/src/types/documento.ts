/**
 * Tipos para Documento y Documentación Requerida SEA.
 */

// =============================================================================
// Categorías Legacy (mantener compatibilidad)
// =============================================================================

export type CategoriaDocumento = 'legal' | 'tecnico' | 'ambiental' | 'cartografia' | 'otro'

export const CATEGORIAS_DOCUMENTO: { value: CategoriaDocumento; label: string; descripcion: string }[] = [
  { value: 'legal', label: 'Legal', descripcion: 'Permisos, contratos, escrituras' },
  { value: 'tecnico', label: 'Tecnico', descripcion: 'Estudios tecnicos, planos, informes' },
  { value: 'ambiental', label: 'Ambiental', descripcion: 'Lineas base, EIA/DIA anteriores' },
  { value: 'cartografia', label: 'Cartografia', descripcion: 'Mapas, imagenes satelitales' },
  { value: 'otro', label: 'Otro', descripcion: 'Documentos varios' },
]

// =============================================================================
// Categorías SEA Específicas
// =============================================================================

export type CategoriaDocumentoSEA =
  // Documentos geográficos/cartográficos
  | 'cartografia_planos'
  // Documentos de personal
  | 'titulo_profesional'
  | 'certificado_consultora'
  | 'certificado_laboratorio'
  // Estudios técnicos especializados
  | 'estudio_aire'
  | 'estudio_agua'
  | 'estudio_suelo'
  | 'estudio_flora'
  | 'estudio_fauna'
  | 'estudio_social'
  | 'estudio_arqueologico'
  | 'estudio_ruido'
  | 'estudio_vibraciones'
  | 'estudio_paisaje'
  | 'estudio_hidrogeologico'
  // Documentos legales y permisos
  | 'resolucion_sanitaria'
  | 'antecedente_pas'
  | 'certificado_pertenencia'
  | 'contrato_servidumbre'
  // Participación ciudadana
  | 'acta_participacion'
  | 'compromiso_voluntario'
  | 'consulta_indigena'
  // Evaluaciones de riesgo
  | 'evaluacion_riesgo'
  | 'plan_emergencia'
  | 'plan_cierre'
  // Otros documentos técnicos
  | 'memoria_tecnica'
  | 'cronograma'
  | 'presupuesto_ambiental'
  | 'otro'

export const CATEGORIAS_DOCUMENTO_SEA: {
  value: CategoriaDocumentoSEA
  label: string
  descripcion: string
  seccion: string
}[] = [
  // Descripción del Proyecto
  { value: 'memoria_tecnica', label: 'Memoria Técnica', descripcion: 'Descripción técnica detallada del proyecto', seccion: 'descripcion_proyecto' },
  { value: 'cartografia_planos', label: 'Cartografía y Planos', descripcion: 'Planos georreferenciados en WGS84', seccion: 'descripcion_proyecto' },
  { value: 'certificado_pertenencia', label: 'Certificados de Pertenencia', descripcion: 'Propiedad o tenencia del terreno', seccion: 'descripcion_proyecto' },
  { value: 'cronograma', label: 'Cronograma', descripcion: 'Cronograma de actividades', seccion: 'descripcion_proyecto' },

  // Línea Base
  { value: 'estudio_aire', label: 'Estudio de Calidad del Aire', descripcion: 'Modelamiento de emisiones atmosféricas', seccion: 'linea_base' },
  { value: 'estudio_agua', label: 'Estudio de Recursos Hídricos', descripcion: 'Modelamiento hidrológico e hidrogeológico', seccion: 'linea_base' },
  { value: 'estudio_suelo', label: 'Estudio de Suelos', descripcion: 'Caracterización edafológica y geoquímica', seccion: 'linea_base' },
  { value: 'estudio_flora', label: 'Estudio de Flora y Vegetación', descripcion: 'Catastro de flora y formaciones vegetacionales', seccion: 'linea_base' },
  { value: 'estudio_fauna', label: 'Estudio de Fauna', descripcion: 'Catastro de fauna terrestre y acuática', seccion: 'linea_base' },
  { value: 'estudio_social', label: 'Línea Base Social', descripcion: 'Caracterización socioeconómica y cultural', seccion: 'linea_base' },
  { value: 'estudio_arqueologico', label: 'Estudio Arqueológico', descripcion: 'Prospección y evaluación de sitios', seccion: 'linea_base' },
  { value: 'estudio_ruido', label: 'Estudio de Ruido', descripcion: 'Modelamiento de ruido y vibraciones', seccion: 'linea_base' },
  { value: 'estudio_vibraciones', label: 'Estudio de Vibraciones', descripcion: 'Análisis de vibraciones', seccion: 'linea_base' },
  { value: 'estudio_paisaje', label: 'Estudio de Paisaje', descripcion: 'Evaluación del paisaje visual', seccion: 'linea_base' },
  { value: 'estudio_hidrogeologico', label: 'Estudio Hidrogeológico', descripcion: 'Caracterización de acuíferos', seccion: 'linea_base' },

  // Predicción de Impactos
  { value: 'evaluacion_riesgo', label: 'Evaluaciones de Riesgo', descripcion: 'Riesgos químicos, salud ocupacional', seccion: 'prediccion_impactos' },

  // Participación Ciudadana
  { value: 'acta_participacion', label: 'Actas de Participación', descripcion: 'Minutas de reuniones con comunidades', seccion: 'participacion' },
  { value: 'compromiso_voluntario', label: 'Compromisos Voluntarios', descripcion: 'Acuerdos firmados con comunidades', seccion: 'participacion' },
  { value: 'consulta_indigena', label: 'Documentación Consulta Indígena', descripcion: 'Proceso de consulta Convenio 169', seccion: 'participacion' },

  // PAS
  { value: 'antecedente_pas', label: 'Antecedentes de PAS', descripcion: 'Documentación técnica para permisos', seccion: 'pas' },
  { value: 'resolucion_sanitaria', label: 'Resoluciones Sanitarias', descripcion: 'Certificados de servicios de salud', seccion: 'pas' },
  { value: 'contrato_servidumbre', label: 'Contratos de Servidumbre', descripcion: 'Servidumbres de paso', seccion: 'pas' },

  // Plan de Cierre
  { value: 'plan_cierre', label: 'Plan de Cierre', descripcion: 'Plan de cierre de faenas', seccion: 'plan_cierre' },
  { value: 'plan_emergencia', label: 'Plan de Emergencia', descripcion: 'Planes de emergencia', seccion: 'plan_cierre' },
  { value: 'presupuesto_ambiental', label: 'Presupuesto Ambiental', descripcion: 'Presupuesto medidas ambientales', seccion: 'plan_cierre' },

  // Anexos
  { value: 'titulo_profesional', label: 'Títulos Profesionales', descripcion: 'Cédulas de especialistas', seccion: 'anexos' },
  { value: 'certificado_consultora', label: 'Certificados de Consultoras', descripcion: 'Permisos de operación', seccion: 'anexos' },
  { value: 'certificado_laboratorio', label: 'Certificados de Laboratorios', descripcion: 'Acreditación de laboratorios', seccion: 'anexos' },
  { value: 'otro', label: 'Otro Documento', descripcion: 'Otros documentos', seccion: 'otros' },
]

export const CATEGORIA_SEA_NOMBRES: Record<CategoriaDocumentoSEA, string> = {
  cartografia_planos: 'Cartografía y Planos',
  titulo_profesional: 'Títulos Profesionales',
  certificado_consultora: 'Certificados de Consultoras',
  certificado_laboratorio: 'Certificados de Laboratorios',
  estudio_aire: 'Estudio de Calidad del Aire',
  estudio_agua: 'Estudio de Recursos Hídricos',
  estudio_suelo: 'Estudio de Suelos',
  estudio_flora: 'Estudio de Flora y Vegetación',
  estudio_fauna: 'Estudio de Fauna',
  estudio_social: 'Línea Base Social',
  estudio_arqueologico: 'Estudio Arqueológico',
  estudio_ruido: 'Estudio de Ruido',
  estudio_vibraciones: 'Estudio de Vibraciones',
  estudio_paisaje: 'Estudio de Paisaje',
  estudio_hidrogeologico: 'Estudio Hidrogeológico',
  resolucion_sanitaria: 'Resoluciones Sanitarias',
  antecedente_pas: 'Antecedentes de PAS',
  certificado_pertenencia: 'Certificados de Pertenencia',
  contrato_servidumbre: 'Contratos de Servidumbre',
  acta_participacion: 'Actas de Participación',
  compromiso_voluntario: 'Compromisos Voluntarios',
  consulta_indigena: 'Documentación Consulta Indígena',
  evaluacion_riesgo: 'Evaluaciones de Riesgo',
  plan_emergencia: 'Plan de Emergencia',
  plan_cierre: 'Plan de Cierre',
  memoria_tecnica: 'Memoria Técnica',
  cronograma: 'Cronograma',
  presupuesto_ambiental: 'Presupuesto Ambiental',
  otro: 'Otro Documento',
}

// =============================================================================
// Estados de Validación
// =============================================================================

export type EstadoValidacion = 'pendiente' | 'subido' | 'validando' | 'aprobado' | 'rechazado' | 'no_aplica'

export const ESTADO_VALIDACION_CONFIG: Record<EstadoValidacion, { label: string; color: string; icon: string }> = {
  pendiente: { label: 'Pendiente', color: 'warning', icon: 'clock' },
  subido: { label: 'Subido', color: 'info', icon: 'upload' },
  validando: { label: 'Validando', color: 'info', icon: 'spinner' },
  aprobado: { label: 'Aprobado', color: 'success', icon: 'check' },
  rechazado: { label: 'Rechazado', color: 'error', icon: 'x' },
  no_aplica: { label: 'No Aplica', color: 'neutral', icon: 'minus' },
}

// =============================================================================
// Interfaces de Documento
// =============================================================================

export interface ValidacionFormato {
  valido: boolean
  errores: string[]
  warnings: string[]
  crs?: string
  geometria_tipo?: string
  num_features?: number
}

export interface Documento {
  id: string
  proyecto_id: number
  nombre: string
  nombre_original: string
  categoria: CategoriaDocumento
  categoria_sea?: CategoriaDocumentoSEA
  descripcion: string | null
  archivo_path: string
  mime_type: string
  tamano_bytes: number
  tamano_mb: number
  checksum_sha256: string | null
  num_paginas?: number
  validacion_formato?: ValidacionFormato | null
  profesional_responsable?: string | null
  fecha_documento?: string | null
  fecha_vigencia?: string | null
  esta_vigente?: boolean
  created_at: string
}

export interface DocumentoCreate {
  nombre: string
  categoria: CategoriaDocumento
  categoria_sea?: CategoriaDocumentoSEA
  descripcion?: string | null
  profesional_responsable?: string | null
  fecha_documento?: string | null
  fecha_vigencia?: string | null
}

export interface DocumentoListResponse {
  items: Documento[]
  total: number
  total_bytes: number
  total_mb: number
}

// =============================================================================
// Interfaces de Documentos Requeridos
// =============================================================================

export interface DocumentoRequeridoEstado {
  requerimiento_id: number
  categoria_sea: CategoriaDocumentoSEA
  nombre_display: string
  descripcion?: string
  notas_sea?: string
  es_obligatorio: boolean
  obligatorio_segun_via: boolean
  seccion_eia?: string
  orden: number
  documento_id?: string
  documento_nombre?: string
  estado_cumplimiento: EstadoValidacion
  formatos_permitidos: string[]
  requiere_crs_wgs84: boolean
}

export interface DocumentosRequeridosResponse {
  proyecto_id: number
  via_evaluacion: 'DIA' | 'EIA'
  items: DocumentoRequeridoEstado[]
  total_requeridos: number
  total_obligatorios: number
  total_subidos: number
}

export interface ValidacionCompletitudResponse {
  proyecto_id: number
  es_completo: boolean
  total_requeridos: number
  total_obligatorios: number
  total_subidos: number
  porcentaje_completitud: number
  obligatorios_faltantes: string[]
  opcionales_faltantes: string[]
  alertas: string[]
  puede_continuar: boolean
}

export interface ValidacionCartografiaResponse {
  documento_id: string
  valido: boolean
  crs_detectado?: string
  crs_es_wgs84: boolean
  tipo_geometria?: string
  num_features: number
  bbox?: number[]
  area_total_ha?: number
  errores: string[]
  warnings: string[]
}

// =============================================================================
// Secciones del EIA
// =============================================================================

export type SeccionEIA =
  | 'descripcion_proyecto'
  | 'linea_base'
  | 'prediccion_impactos'
  | 'medidas_mitigacion'
  | 'plan_seguimiento'
  | 'plan_cierre'
  | 'participacion'
  | 'pas'
  | 'anexos'
  | 'otros'

export const SECCIONES_EIA: { value: SeccionEIA; label: string; orden: number }[] = [
  { value: 'descripcion_proyecto', label: 'Descripción del Proyecto', orden: 1 },
  { value: 'linea_base', label: 'Línea de Base', orden: 2 },
  { value: 'prediccion_impactos', label: 'Predicción de Impactos', orden: 3 },
  { value: 'medidas_mitigacion', label: 'Plan de Medidas', orden: 4 },
  { value: 'plan_seguimiento', label: 'Plan de Seguimiento', orden: 5 },
  { value: 'plan_cierre', label: 'Plan de Cierre', orden: 6 },
  { value: 'participacion', label: 'Participación Ciudadana', orden: 7 },
  { value: 'pas', label: 'Permisos Ambientales Sectoriales', orden: 8 },
  { value: 'anexos', label: 'Anexos', orden: 9 },
  { value: 'otros', label: 'Otros', orden: 10 },
]

// =============================================================================
// Helpers
// =============================================================================

export function getNombreCategoriaSEA(categoria: CategoriaDocumentoSEA): string {
  return CATEGORIA_SEA_NOMBRES[categoria] || categoria
}

export function getSeccionPorCategoria(categoria: CategoriaDocumentoSEA): SeccionEIA {
  const cat = CATEGORIAS_DOCUMENTO_SEA.find((c) => c.value === categoria)
  return (cat?.seccion as SeccionEIA) || 'otros'
}

// Tipo para documentos agrupados por sección
export type DocumentosPorSeccion = Record<SeccionEIA, DocumentoRequeridoEstado[]>

export function getDocumentosPorSeccion(
  documentos: DocumentoRequeridoEstado[]
): DocumentosPorSeccion {
  const resultado: Record<SeccionEIA, DocumentoRequeridoEstado[]> = {
    descripcion_proyecto: [],
    linea_base: [],
    prediccion_impactos: [],
    medidas_mitigacion: [],
    plan_seguimiento: [],
    plan_cierre: [],
    participacion: [],
    pas: [],
    anexos: [],
    otros: [],
  }

  for (const doc of documentos) {
    const seccion = (doc.seccion_eia as SeccionEIA) || 'otros'
    if (resultado[seccion]) {
      resultado[seccion].push(doc)
    } else {
      resultado.otros.push(doc)
    }
  }

  return resultado
}
