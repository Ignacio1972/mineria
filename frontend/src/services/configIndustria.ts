/**
 * Servicio API para Configuracion por Industria.
 */
import api from './api'
import type {
  TiposProyectoListResponse,
  TipoProyectoConSubtipos,
  SubtipoProyecto,
  ConfigIndustriaCompleta,
  ConfigIndustriaResumen,
  UmbralSEIA,
  EvaluarUmbralRequest,
  EvaluarUmbralResponse,
  PASListResponse,
  PASAplicable,
  NormativaListResponse,
  OAECAPorTipo,
  ImpactoPorTipo,
  AnexoPorTipo,
  PreguntasListResponse,
  ArbolPregunta,
  ProgresoPreguntas,
} from '@/types'

const BASE_URL = '/config'

export const configIndustriaService = {
  // =========================================================================
  // Tipos de Proyecto
  // =========================================================================

  /**
   * Lista todos los tipos de proyecto (industrias).
   */
  async listarTipos(soloActivos = true): Promise<TiposProyectoListResponse> {
    const { data } = await api.get<TiposProyectoListResponse>(`${BASE_URL}/tipos`, {
      params: { solo_activos: soloActivos }
    })
    return data
  },

  /**
   * Obtiene un tipo de proyecto por codigo.
   */
  async obtenerTipo(codigo: string): Promise<TipoProyectoConSubtipos> {
    const { data } = await api.get<TipoProyectoConSubtipos>(`${BASE_URL}/tipos/${codigo}`)
    return data
  },

  // =========================================================================
  // Subtipos
  // =========================================================================

  /**
   * Lista los subtipos de un tipo de proyecto.
   */
  async listarSubtipos(tipoCodigo: string, soloActivos = true): Promise<SubtipoProyecto[]> {
    const { data } = await api.get<SubtipoProyecto[]>(
      `${BASE_URL}/tipos/${tipoCodigo}/subtipos`,
      { params: { solo_activos: soloActivos } }
    )
    return data
  },

  // =========================================================================
  // Configuracion Completa
  // =========================================================================

  /**
   * Obtiene la configuracion completa de una industria.
   */
  async obtenerConfigCompleta(
    tipoCodigo: string,
    subtipoCodigo?: string
  ): Promise<ConfigIndustriaCompleta> {
    const { data } = await api.get<ConfigIndustriaCompleta>(
      `${BASE_URL}/tipos/${tipoCodigo}/config`,
      { params: { subtipo_codigo: subtipoCodigo } }
    )
    return data
  },

  /**
   * Obtiene resumen de configuracion de todas las industrias.
   */
  async obtenerResumenConfig(): Promise<ConfigIndustriaResumen[]> {
    const { data } = await api.get<ConfigIndustriaResumen[]>(`${BASE_URL}/resumen`)
    return data
  },

  // =========================================================================
  // Umbrales SEIA
  // =========================================================================

  /**
   * Lista los umbrales SEIA de un tipo de proyecto.
   */
  async listarUmbrales(tipoCodigo: string, subtipoCodigo?: string): Promise<UmbralSEIA[]> {
    const { data } = await api.get<UmbralSEIA[]>(
      `${BASE_URL}/tipos/${tipoCodigo}/umbrales`,
      { params: { subtipo_codigo: subtipoCodigo } }
    )
    return data
  },

  /**
   * Evalua si un proyecto cumple umbral de ingreso SEIA.
   */
  async evaluarUmbral(request: EvaluarUmbralRequest): Promise<EvaluarUmbralResponse> {
    const { data } = await api.post<EvaluarUmbralResponse>(
      `${BASE_URL}/evaluar-umbral`,
      request
    )
    return data
  },

  // =========================================================================
  // PAS
  // =========================================================================

  /**
   * Lista los PAS tipicos de un tipo de proyecto.
   */
  async listarPAS(tipoCodigo: string, subtipoCodigo?: string): Promise<PASListResponse> {
    const { data } = await api.get<PASListResponse>(
      `${BASE_URL}/tipos/${tipoCodigo}/pas`,
      { params: { subtipo_codigo: subtipoCodigo } }
    )
    return data
  },

  /**
   * Identifica los PAS aplicables segun caracteristicas del proyecto.
   */
  async identificarPASAplicables(
    tipoCodigo: string,
    caracteristicas: Record<string, unknown>,
    subtipoCodigo?: string
  ): Promise<PASAplicable[]> {
    const { data } = await api.post<PASAplicable[]>(
      `${BASE_URL}/tipos/${tipoCodigo}/pas/aplicables`,
      caracteristicas,
      { params: { subtipo_codigo: subtipoCodigo } }
    )
    return data
  },

  // =========================================================================
  // Normativa
  // =========================================================================

  /**
   * Lista la normativa aplicable a un tipo de proyecto.
   */
  async listarNormativa(tipoCodigo: string): Promise<NormativaListResponse> {
    const { data } = await api.get<NormativaListResponse>(
      `${BASE_URL}/tipos/${tipoCodigo}/normativa`
    )
    return data
  },

  // =========================================================================
  // OAECA
  // =========================================================================

  /**
   * Lista los OAECA relevantes para un tipo de proyecto.
   */
  async listarOAECA(tipoCodigo: string): Promise<OAECAPorTipo[]> {
    const { data } = await api.get<OAECAPorTipo[]>(`${BASE_URL}/tipos/${tipoCodigo}/oaeca`)
    return data
  },

  // =========================================================================
  // Impactos
  // =========================================================================

  /**
   * Lista los impactos tipicos de un tipo de proyecto.
   */
  async listarImpactos(tipoCodigo: string, subtipoCodigo?: string): Promise<ImpactoPorTipo[]> {
    const { data } = await api.get<ImpactoPorTipo[]>(
      `${BASE_URL}/tipos/${tipoCodigo}/impactos`,
      { params: { subtipo_codigo: subtipoCodigo } }
    )
    return data
  },

  // =========================================================================
  // Anexos
  // =========================================================================

  /**
   * Lista los anexos requeridos para un tipo de proyecto.
   */
  async listarAnexos(tipoCodigo: string, subtipoCodigo?: string): Promise<AnexoPorTipo[]> {
    const { data } = await api.get<AnexoPorTipo[]>(
      `${BASE_URL}/tipos/${tipoCodigo}/anexos`,
      { params: { subtipo_codigo: subtipoCodigo } }
    )
    return data
  },

  /**
   * Identifica los anexos aplicables segun caracteristicas del proyecto.
   */
  async identificarAnexosAplicables(
    tipoCodigo: string,
    caracteristicas: Record<string, unknown>,
    subtipoCodigo?: string
  ): Promise<AnexoPorTipo[]> {
    const { data } = await api.post<AnexoPorTipo[]>(
      `${BASE_URL}/tipos/${tipoCodigo}/anexos/aplicables`,
      caracteristicas,
      { params: { subtipo_codigo: subtipoCodigo } }
    )
    return data
  },

  // =========================================================================
  // Arbol de Preguntas
  // =========================================================================

  /**
   * Lista las preguntas del arbol para un tipo de proyecto.
   */
  async listarPreguntas(tipoCodigo: string, subtipoCodigo?: string): Promise<PreguntasListResponse> {
    const { data } = await api.get<PreguntasListResponse>(
      `${BASE_URL}/tipos/${tipoCodigo}/preguntas`,
      { params: { subtipo_codigo: subtipoCodigo } }
    )
    return data
  },

  /**
   * Obtiene la siguiente pregunta del arbol segun respuestas previas.
   */
  async obtenerSiguientePregunta(
    tipoCodigo: string,
    respuestasPrevias: Record<string, unknown>,
    subtipoCodigo?: string
  ): Promise<ArbolPregunta | null> {
    const { data } = await api.post<ArbolPregunta | null>(
      `${BASE_URL}/tipos/${tipoCodigo}/preguntas/siguiente`,
      respuestasPrevias,
      { params: { subtipo_codigo: subtipoCodigo } }
    )
    return data
  },

  /**
   * Calcula el progreso de recopilacion.
   */
  async calcularProgreso(
    tipoCodigo: string,
    respuestasPrevias: Record<string, unknown>,
    subtipoCodigo?: string
  ): Promise<ProgresoPreguntas> {
    const { data } = await api.post<ProgresoPreguntas>(
      `${BASE_URL}/tipos/${tipoCodigo}/preguntas/progreso`,
      respuestasPrevias,
      { params: { subtipo_codigo: subtipoCodigo } }
    )
    return data
  },
}

export default configIndustriaService
