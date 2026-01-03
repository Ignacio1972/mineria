/**
 * Store Pinia para Ficha Acumulativa del Proyecto.
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { fichaService } from '@/services/ficha'
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
  CATEGORIA_LABELS,
} from '@/types'

export const useFichaStore = defineStore('ficha', () => {
  // ==========================================================================
  // Estado
  // ==========================================================================

  // Proyecto actual
  const proyectoId = ref<number | null>(null)

  // Ficha completa
  const ficha = ref<FichaProyecto | null>(null)

  // Caracteristicas separadas para edicion
  const caracteristicas = ref<Caracteristica[]>([])
  const caracteristicasPorCategoria = ref<CaracteristicasPorCategoria | null>(null)

  // PAS
  const pas = ref<PASProyecto[]>([])

  // Analisis Art. 11
  const analisisArt11 = ref<AnalisisArt11[]>([])

  // Diagnostico
  const diagnostico = ref<Diagnostico | null>(null)

  // Progreso
  const progreso = ref<ProgresoFicha | null>(null)

  // Estado de carga
  const cargando = ref(false)
  const guardando = ref(false)
  const error = ref<string | null>(null)

  // ==========================================================================
  // Computed
  // ==========================================================================

  const tieneFicha = computed(() => ficha.value !== null)

  const nombreProyecto = computed(() => ficha.value?.nombre || '')

  const estadoProyecto = computed(() => ficha.value?.estado || '')

  const tipoProyecto = computed(() => ({
    codigo: ficha.value?.tipo_codigo || null,
    nombre: ficha.value?.tipo_nombre || null,
  }))

  const subtipoProyecto = computed(() => ({
    codigo: ficha.value?.subtipo_codigo || null,
    nombre: ficha.value?.subtipo_nombre || null,
  }))

  const ubicacion = computed(() => ficha.value?.ubicacion || null)

  const porcentajeProgreso = computed(() => progreso.value?.porcentaje_completitud || 0)

  const camposFaltantes = computed(() => progreso.value?.campos_faltantes_obligatorios || [])

  const viaSugerida = computed(() => diagnostico.value?.via_sugerida || null)

  const confianzaDiagnostico = computed(() => diagnostico.value?.confianza || null)

  const literalesGatillados = computed(() => diagnostico.value?.literales_gatillados || [])

  const totalPAS = computed(() => pas.value.length)

  const pasRequeridos = computed(() =>
    pas.value.filter(p => p.estado === 'requerido' || p.obligatorio)
  )

  const totalCaracteristicas = computed(() => caracteristicas.value.length)

  const caracteristicasValidadas = computed(() =>
    caracteristicas.value.filter(c => c.validado).length
  )

  // ==========================================================================
  // Acciones - Ficha
  // ==========================================================================

  /**
   * Carga la ficha completa del proyecto.
   */
  async function cargarFicha(id: number): Promise<FichaProyecto | null> {
    cargando.value = true
    error.value = null
    proyectoId.value = id

    try {
      ficha.value = await fichaService.obtenerFichaCompleta(id)

      // Extraer datos relacionados
      if (ficha.value) {
        caracteristicasPorCategoria.value = ficha.value.caracteristicas
        pas.value = ficha.value.pas
        analisisArt11.value = Object.values(ficha.value.analisis_art11)
        diagnostico.value = ficha.value.diagnostico_actual
      }

      return ficha.value
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error cargando ficha'
      throw e
    } finally {
      cargando.value = false
    }
  }

  /**
   * Recarga la ficha actual.
   */
  async function recargarFicha(): Promise<void> {
    if (proyectoId.value) {
      await cargarFicha(proyectoId.value)
    }
  }

  // ==========================================================================
  // Acciones - Caracteristicas
  // ==========================================================================

  /**
   * Carga las caracteristicas del proyecto.
   */
  async function cargarCaracteristicas(categoria?: CategoriaCaracteristica): Promise<void> {
    if (!proyectoId.value) return

    cargando.value = true
    try {
      caracteristicas.value = await fichaService.listarCaracteristicas(
        proyectoId.value,
        categoria
      )
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error cargando caracteristicas'
      throw e
    } finally {
      cargando.value = false
    }
  }

  /**
   * Carga caracteristicas agrupadas por categoria.
   */
  async function cargarCaracteristicasPorCategoria(): Promise<void> {
    if (!proyectoId.value) return

    cargando.value = true
    try {
      caracteristicasPorCategoria.value = await fichaService.obtenerCaracteristicasPorCategoria(
        proyectoId.value
      )
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error cargando caracteristicas'
      throw e
    } finally {
      cargando.value = false
    }
  }

  /**
   * Guarda una caracteristica.
   */
  async function guardarCaracteristica(data: CaracteristicaCreate): Promise<Caracteristica | null> {
    if (!proyectoId.value) return null

    guardando.value = true
    try {
      const caracteristica = await fichaService.guardarCaracteristica(proyectoId.value, data)

      // Actualizar lista local
      const index = caracteristicas.value.findIndex(
        c => c.categoria === data.categoria && c.clave === data.clave
      )
      if (index >= 0) {
        caracteristicas.value[index] = caracteristica
      } else {
        caracteristicas.value.push(caracteristica)
      }

      return caracteristica
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error guardando caracteristica'
      throw e
    } finally {
      guardando.value = false
    }
  }

  /**
   * Guarda multiples caracteristicas.
   */
  async function guardarCaracteristicasBulk(
    datos: CaracteristicaCreate[]
  ): Promise<Caracteristica[]> {
    if (!proyectoId.value) return []

    guardando.value = true
    try {
      const result = await fichaService.guardarCaracteristicasBulk(proyectoId.value, datos)

      // Recargar caracteristicas
      await cargarCaracteristicas()

      return result
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error guardando caracteristicas'
      throw e
    } finally {
      guardando.value = false
    }
  }

  /**
   * Valida una caracteristica.
   */
  async function validarCaracteristica(
    categoria: CategoriaCaracteristica,
    clave: string,
    validadoPor: string
  ): Promise<void> {
    if (!proyectoId.value) return

    guardando.value = true
    try {
      const caracteristica = await fichaService.validarCaracteristica(
        proyectoId.value,
        categoria,
        clave,
        validadoPor
      )

      // Actualizar lista local
      const index = caracteristicas.value.findIndex(
        c => c.categoria === categoria && c.clave === clave
      )
      if (index >= 0) {
        caracteristicas.value[index] = caracteristica
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error validando caracteristica'
      throw e
    } finally {
      guardando.value = false
    }
  }

  /**
   * Elimina una caracteristica.
   */
  async function eliminarCaracteristica(
    categoria: CategoriaCaracteristica,
    clave: string
  ): Promise<void> {
    if (!proyectoId.value) return

    guardando.value = true
    try {
      await fichaService.eliminarCaracteristica(proyectoId.value, categoria, clave)

      // Eliminar de lista local
      caracteristicas.value = caracteristicas.value.filter(
        c => !(c.categoria === categoria && c.clave === clave)
      )
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error eliminando caracteristica'
      throw e
    } finally {
      guardando.value = false
    }
  }

  // ==========================================================================
  // Acciones - PAS
  // ==========================================================================

  /**
   * Carga los PAS del proyecto.
   */
  async function cargarPAS(): Promise<void> {
    if (!proyectoId.value) return

    cargando.value = true
    try {
      pas.value = await fichaService.listarPAS(proyectoId.value)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error cargando PAS'
      throw e
    } finally {
      cargando.value = false
    }
  }

  /**
   * Guarda un PAS.
   */
  async function guardarPAS(data: PASProyectoCreate): Promise<PASProyecto | null> {
    if (!proyectoId.value) return null

    guardando.value = true
    try {
      const nuevoPAS = await fichaService.guardarPAS(proyectoId.value, data)

      // Actualizar lista local
      const index = pas.value.findIndex(p => p.articulo === data.articulo)
      if (index >= 0) {
        pas.value[index] = nuevoPAS
      } else {
        pas.value.push(nuevoPAS)
      }

      return nuevoPAS
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error guardando PAS'
      throw e
    } finally {
      guardando.value = false
    }
  }

  /**
   * Actualiza el estado de un PAS.
   */
  async function actualizarEstadoPAS(
    articulo: number,
    data: PASProyectoUpdate
  ): Promise<void> {
    if (!proyectoId.value) return

    guardando.value = true
    try {
      const pasActualizado = await fichaService.actualizarPAS(
        proyectoId.value,
        articulo,
        data
      )

      // Actualizar lista local
      const index = pas.value.findIndex(p => p.articulo === articulo)
      if (index >= 0) {
        pas.value[index] = pasActualizado
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error actualizando PAS'
      throw e
    } finally {
      guardando.value = false
    }
  }

  // ==========================================================================
  // Acciones - Analisis Art. 11
  // ==========================================================================

  /**
   * Carga el analisis Art. 11.
   */
  async function cargarAnalisisArt11(): Promise<void> {
    if (!proyectoId.value) return

    cargando.value = true
    try {
      analisisArt11.value = await fichaService.listarAnalisisArt11(proyectoId.value)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error cargando analisis Art. 11'
      throw e
    } finally {
      cargando.value = false
    }
  }

  /**
   * Guarda analisis de un literal.
   */
  async function guardarAnalisisLiteral(data: AnalisisArt11Create): Promise<AnalisisArt11 | null> {
    if (!proyectoId.value) return null

    guardando.value = true
    try {
      const analisis = await fichaService.guardarAnalisisArt11(proyectoId.value, data)

      // Actualizar lista local
      const index = analisisArt11.value.findIndex(a => a.literal === data.literal)
      if (index >= 0) {
        analisisArt11.value[index] = analisis
      } else {
        analisisArt11.value.push(analisis)
      }

      return analisis
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error guardando analisis'
      throw e
    } finally {
      guardando.value = false
    }
  }

  // ==========================================================================
  // Acciones - Diagnostico y Progreso
  // ==========================================================================

  /**
   * Carga el diagnostico actual.
   */
  async function cargarDiagnostico(): Promise<void> {
    if (!proyectoId.value) return

    try {
      diagnostico.value = await fichaService.obtenerDiagnostico(proyectoId.value)
    } catch {
      // No hay diagnostico aun
      diagnostico.value = null
    }
  }

  /**
   * Carga el progreso de la ficha.
   */
  async function cargarProgreso(): Promise<void> {
    if (!proyectoId.value) return

    try {
      progreso.value = await fichaService.obtenerProgreso(proyectoId.value)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error cargando progreso'
    }
  }

  // ==========================================================================
  // Acciones - Respuestas Asistente
  // ==========================================================================

  /**
   * Guarda respuestas del asistente.
   */
  async function guardarRespuestasAsistente(
    respuestas: GuardarRespuestaAsistente[]
  ): Promise<void> {
    if (!proyectoId.value) return

    guardando.value = true
    try {
      await fichaService.guardarRespuestasAsistente(proyectoId.value, respuestas)

      // Recargar caracteristicas
      await cargarCaracteristicas()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error guardando respuestas'
      throw e
    } finally {
      guardando.value = false
    }
  }

  // ==========================================================================
  // Helpers
  // ==========================================================================

  /**
   * Obtiene caracteristicas de una categoria.
   */
  function getCaracteristicasCategoria(categoria: CategoriaCaracteristica): Caracteristica[] {
    return caracteristicas.value.filter(c => c.categoria === categoria)
  }

  /**
   * Obtiene una caracteristica por clave.
   */
  function getCaracteristica(
    categoria: CategoriaCaracteristica,
    clave: string
  ): Caracteristica | undefined {
    return caracteristicas.value.find(
      c => c.categoria === categoria && c.clave === clave
    )
  }

  /**
   * Obtiene analisis de un literal.
   */
  function getAnalisisLiteral(literal: string): AnalisisArt11 | undefined {
    return analisisArt11.value.find(a => a.literal === literal)
  }

  /**
   * Obtiene PAS por articulo.
   */
  function getPAS(articulo: number): PASProyecto | undefined {
    return pas.value.find(p => p.articulo === articulo)
  }

  // ==========================================================================
  // Limpiar
  // ==========================================================================

  function limpiar(): void {
    proyectoId.value = null
    ficha.value = null
    caracteristicas.value = []
    caracteristicasPorCategoria.value = null
    pas.value = []
    analisisArt11.value = []
    diagnostico.value = null
    progreso.value = null
    error.value = null
  }

  // ==========================================================================
  // Return
  // ==========================================================================

  return {
    // Estado
    proyectoId,
    ficha,
    caracteristicas,
    caracteristicasPorCategoria,
    pas,
    analisisArt11,
    diagnostico,
    progreso,
    cargando,
    guardando,
    error,

    // Computed
    tieneFicha,
    nombreProyecto,
    estadoProyecto,
    tipoProyecto,
    subtipoProyecto,
    ubicacion,
    porcentajeProgreso,
    camposFaltantes,
    viaSugerida,
    confianzaDiagnostico,
    literalesGatillados,
    totalPAS,
    pasRequeridos,
    totalCaracteristicas,
    caracteristicasValidadas,

    // Acciones - Ficha
    cargarFicha,
    recargarFicha,

    // Acciones - Caracteristicas
    cargarCaracteristicas,
    cargarCaracteristicasPorCategoria,
    guardarCaracteristica,
    guardarCaracteristicasBulk,
    validarCaracteristica,
    eliminarCaracteristica,

    // Acciones - PAS
    cargarPAS,
    guardarPAS,
    actualizarEstadoPAS,

    // Acciones - Analisis Art. 11
    cargarAnalisisArt11,
    guardarAnalisisLiteral,

    // Acciones - Diagnostico y Progreso
    cargarDiagnostico,
    cargarProgreso,

    // Acciones - Respuestas Asistente
    guardarRespuestasAsistente,

    // Helpers
    getCaracteristicasCategoria,
    getCaracteristica,
    getAnalisisLiteral,
    getPAS,

    // Limpiar
    limpiar,
  }
})
