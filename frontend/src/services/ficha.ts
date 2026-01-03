/**
 * Servicio API para Ficha Acumulativa del Proyecto.
 */
import api from './api'
import type {
  FichaProyecto,
  FichaResumen,
  Caracteristica,
  CaracteristicaCreate,
  CaracteristicaUpdate,
  CaracteristicasPorCategoria,
  CategoriaCaracteristica,
  PASProyecto,
  PASProyectoCreate,
  PASProyectoUpdate,
  AnalisisArt11,
  AnalisisArt11Create,
  Diagnostico,
  ProgresoFicha,
  GuardarRespuestaAsistente,
  GuardarRespuestasResponse,
} from '@/types'

const BASE_URL = '/ficha'

export const fichaService = {
  // =========================================================================
  // Ficha Consolidada
  // =========================================================================

  /**
   * Obtiene la ficha completa del proyecto.
   */
  async obtenerFichaCompleta(proyectoId: number): Promise<FichaProyecto> {
    const { data } = await api.get<FichaProyecto>(`${BASE_URL}/${proyectoId}`)
    return data
  },

  /**
   * Obtiene resumen de la ficha para listados.
   */
  async obtenerFichaResumen(proyectoId: number): Promise<FichaResumen> {
    const { data } = await api.get<FichaResumen>(`${BASE_URL}/${proyectoId}/resumen`)
    return data
  },

  // =========================================================================
  // Caracteristicas
  // =========================================================================

  /**
   * Lista las caracteristicas del proyecto.
   */
  async listarCaracteristicas(
    proyectoId: number,
    categoria?: CategoriaCaracteristica
  ): Promise<Caracteristica[]> {
    const { data } = await api.get<Caracteristica[]>(
      `${BASE_URL}/${proyectoId}/caracteristicas`,
      { params: { categoria } }
    )
    return data
  },

  /**
   * Obtiene caracteristicas agrupadas por categoria.
   */
  async obtenerCaracteristicasPorCategoria(
    proyectoId: number
  ): Promise<CaracteristicasPorCategoria> {
    const { data } = await api.get<CaracteristicasPorCategoria>(
      `${BASE_URL}/${proyectoId}/caracteristicas/por-categoria`
    )
    return data
  },

  /**
   * Crea o actualiza una caracteristica.
   */
  async guardarCaracteristica(
    proyectoId: number,
    data: CaracteristicaCreate
  ): Promise<Caracteristica> {
    const { data: result } = await api.post<Caracteristica>(
      `${BASE_URL}/${proyectoId}/caracteristicas`,
      data
    )
    return result
  },

  /**
   * Crea multiples caracteristicas.
   */
  async guardarCaracteristicasBulk(
    proyectoId: number,
    caracteristicas: CaracteristicaCreate[]
  ): Promise<Caracteristica[]> {
    const { data } = await api.post<Caracteristica[]>(
      `${BASE_URL}/${proyectoId}/caracteristicas/bulk`,
      { caracteristicas }
    )
    return data
  },

  /**
   * Obtiene una caracteristica especifica.
   */
  async obtenerCaracteristica(
    proyectoId: number,
    categoria: CategoriaCaracteristica,
    clave: string
  ): Promise<Caracteristica> {
    const { data } = await api.get<Caracteristica>(
      `${BASE_URL}/${proyectoId}/caracteristicas/${categoria}/${clave}`
    )
    return data
  },

  /**
   * Actualiza una caracteristica existente.
   */
  async actualizarCaracteristica(
    proyectoId: number,
    categoria: CategoriaCaracteristica,
    clave: string,
    data: CaracteristicaUpdate
  ): Promise<Caracteristica> {
    const { data: result } = await api.patch<Caracteristica>(
      `${BASE_URL}/${proyectoId}/caracteristicas/${categoria}/${clave}`,
      data
    )
    return result
  },

  /**
   * Valida una caracteristica.
   */
  async validarCaracteristica(
    proyectoId: number,
    categoria: CategoriaCaracteristica,
    clave: string,
    validadoPor: string
  ): Promise<Caracteristica> {
    const { data } = await api.post<Caracteristica>(
      `${BASE_URL}/${proyectoId}/caracteristicas/${categoria}/${clave}/validar`,
      null,
      { params: { validado_por: validadoPor } }
    )
    return data
  },

  /**
   * Elimina una caracteristica.
   */
  async eliminarCaracteristica(
    proyectoId: number,
    categoria: CategoriaCaracteristica,
    clave: string
  ): Promise<void> {
    await api.delete(`${BASE_URL}/${proyectoId}/caracteristicas/${categoria}/${clave}`)
  },

  // =========================================================================
  // PAS del Proyecto
  // =========================================================================

  /**
   * Lista los PAS del proyecto.
   */
  async listarPAS(proyectoId: number): Promise<PASProyecto[]> {
    const { data } = await api.get<PASProyecto[]>(`${BASE_URL}/${proyectoId}/pas`)
    return data
  },

  /**
   * Crea o actualiza un PAS.
   */
  async guardarPAS(proyectoId: number, data: PASProyectoCreate): Promise<PASProyecto> {
    const { data: result } = await api.post<PASProyecto>(
      `${BASE_URL}/${proyectoId}/pas`,
      data
    )
    return result
  },

  /**
   * Obtiene un PAS especifico.
   */
  async obtenerPAS(proyectoId: number, articulo: number): Promise<PASProyecto> {
    const { data } = await api.get<PASProyecto>(`${BASE_URL}/${proyectoId}/pas/${articulo}`)
    return data
  },

  /**
   * Actualiza el estado de un PAS.
   */
  async actualizarPAS(
    proyectoId: number,
    articulo: number,
    data: PASProyectoUpdate
  ): Promise<PASProyecto> {
    const { data: result } = await api.patch<PASProyecto>(
      `${BASE_URL}/${proyectoId}/pas/${articulo}`,
      data
    )
    return result
  },

  // =========================================================================
  // Analisis Art. 11
  // =========================================================================

  /**
   * Lista el analisis Art. 11 del proyecto.
   */
  async listarAnalisisArt11(proyectoId: number): Promise<AnalisisArt11[]> {
    const { data } = await api.get<AnalisisArt11[]>(`${BASE_URL}/${proyectoId}/art11`)
    return data
  },

  /**
   * Obtiene analisis de un literal especifico.
   */
  async obtenerAnalisisLiteral(proyectoId: number, literal: string): Promise<AnalisisArt11> {
    const { data } = await api.get<AnalisisArt11>(
      `${BASE_URL}/${proyectoId}/art11/${literal}`
    )
    return data
  },

  /**
   * Crea o actualiza analisis de literal.
   */
  async guardarAnalisisArt11(
    proyectoId: number,
    data: AnalisisArt11Create
  ): Promise<AnalisisArt11> {
    const { data: result } = await api.post<AnalisisArt11>(
      `${BASE_URL}/${proyectoId}/art11`,
      data
    )
    return result
  },

  // =========================================================================
  // Diagnostico
  // =========================================================================

  /**
   * Obtiene el diagnostico actual del proyecto.
   */
  async obtenerDiagnostico(proyectoId: number): Promise<Diagnostico> {
    const { data } = await api.get<Diagnostico>(`${BASE_URL}/${proyectoId}/diagnostico`)
    return data
  },

  // =========================================================================
  // Progreso
  // =========================================================================

  /**
   * Obtiene el progreso de completitud de la ficha.
   */
  async obtenerProgreso(proyectoId: number): Promise<ProgresoFicha> {
    const { data } = await api.get<ProgresoFicha>(`${BASE_URL}/${proyectoId}/progreso`)
    return data
  },

  // =========================================================================
  // Respuestas del Asistente
  // =========================================================================

  /**
   * Guarda respuestas del asistente en la ficha.
   */
  async guardarRespuestasAsistente(
    proyectoId: number,
    respuestas: GuardarRespuestaAsistente[]
  ): Promise<GuardarRespuestasResponse> {
    const { data } = await api.post<GuardarRespuestasResponse>(
      `${BASE_URL}/${proyectoId}/respuestas-asistente`,
      respuestas
    )
    return data
  },
}

export default fichaService
