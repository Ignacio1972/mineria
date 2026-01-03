/**
 * Store Pinia para Configuracion por Industria.
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { configIndustriaService } from '@/services/configIndustria'
import type {
  TipoProyectoConSubtipos,
  SubtipoProyecto,
  ConfigIndustriaCompleta,
  ConfigIndustriaResumen,
  UmbralSEIA,
  EvaluarUmbralResponse,
  PASPorTipo,
  PASAplicable,
  NormativaPorTipo,
  OAECAPorTipo,
  ImpactoPorTipo,
  AnexoPorTipo,
  ArbolPregunta,
  ProgresoPreguntas,
} from '@/types'

export const useConfigIndustriaStore = defineStore('configIndustria', () => {
  // ==========================================================================
  // Estado
  // ==========================================================================

  // Cache de tipos de proyecto
  const tipos = ref<TipoProyectoConSubtipos[]>([])
  const tiposCargados = ref(false)

  // Configuracion actual (por tipo/subtipo seleccionado)
  const configActual = ref<ConfigIndustriaCompleta | null>(null)
  const tipoActualCodigo = ref<string | null>(null)
  const subtipoActualCodigo = ref<string | null>(null)

  // Resumenes de configuracion
  const resumenes = ref<ConfigIndustriaResumen[]>([])

  // Estado de carga
  const cargando = ref(false)
  const error = ref<string | null>(null)

  // Cache de evaluaciones de umbral
  const ultimaEvaluacionUmbral = ref<EvaluarUmbralResponse | null>(null)

  // Cache de PAS aplicables
  const pasAplicables = ref<PASAplicable[]>([])

  // Progreso de preguntas
  const progresoPreguntas = ref<ProgresoPreguntas | null>(null)
  const preguntaActual = ref<ArbolPregunta | null>(null)
  const respuestasPreguntas = ref<Record<string, unknown>>({})

  // ==========================================================================
  // Computed
  // ==========================================================================

  const tipoActual = computed(() => {
    if (!tipoActualCodigo.value || !tipos.value.length) return null
    return tipos.value.find(t => t.codigo === tipoActualCodigo.value) || null
  })

  const subtiposDisponibles = computed(() => {
    return configActual.value?.subtipos_disponibles || []
  })

  const umbralesActuales = computed(() => {
    return configActual.value?.umbrales || []
  })

  const pasActuales = computed(() => {
    return configActual.value?.pas || []
  })

  const normativaActual = computed(() => {
    return configActual.value?.normativa || []
  })

  const oaecaActuales = computed(() => {
    return configActual.value?.oaeca || []
  })

  const impactosActuales = computed(() => {
    return configActual.value?.impactos || []
  })

  const anexosActuales = computed(() => {
    return configActual.value?.anexos || []
  })

  const preguntasActuales = computed(() => {
    return configActual.value?.preguntas || []
  })

  const tieneConfigCargada = computed(() => configActual.value !== null)

  // ==========================================================================
  // Acciones - Tipos
  // ==========================================================================

  /**
   * Carga todos los tipos de proyecto.
   */
  async function cargarTipos(forzar = false): Promise<void> {
    if (tiposCargados.value && !forzar) return

    cargando.value = true
    error.value = null

    try {
      const response = await configIndustriaService.listarTipos()
      tipos.value = response.tipos
      tiposCargados.value = true
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error cargando tipos'
      throw e
    } finally {
      cargando.value = false
    }
  }

  /**
   * Obtiene un tipo por codigo.
   */
  async function obtenerTipo(codigo: string): Promise<TipoProyectoConSubtipos | null> {
    // Buscar en cache
    const cached = tipos.value.find(t => t.codigo === codigo)
    if (cached) return cached

    try {
      return await configIndustriaService.obtenerTipo(codigo)
    } catch {
      return null
    }
  }

  // ==========================================================================
  // Acciones - Configuracion
  // ==========================================================================

  /**
   * Carga la configuracion completa de una industria.
   */
  async function cargarConfigCompleta(
    tipoCodigo: string,
    subtipoCodigo?: string
  ): Promise<ConfigIndustriaCompleta | null> {
    cargando.value = true
    error.value = null

    try {
      const config = await configIndustriaService.obtenerConfigCompleta(tipoCodigo, subtipoCodigo)
      configActual.value = config
      tipoActualCodigo.value = tipoCodigo
      subtipoActualCodigo.value = subtipoCodigo || null
      return config
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error cargando configuracion'
      throw e
    } finally {
      cargando.value = false
    }
  }

  /**
   * Carga resumen de todas las industrias.
   */
  async function cargarResumenes(): Promise<void> {
    cargando.value = true
    error.value = null

    try {
      resumenes.value = await configIndustriaService.obtenerResumenConfig()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error cargando resumenes'
      throw e
    } finally {
      cargando.value = false
    }
  }

  /**
   * Cambia el tipo de proyecto actual.
   */
  async function seleccionarTipo(tipoCodigo: string): Promise<void> {
    await cargarConfigCompleta(tipoCodigo)
    // Resetear estado de preguntas
    respuestasPreguntas.value = {}
    progresoPreguntas.value = null
    preguntaActual.value = null
    pasAplicables.value = []
    ultimaEvaluacionUmbral.value = null
  }

  /**
   * Cambia el subtipo de proyecto actual.
   */
  async function seleccionarSubtipo(subtipoCodigo: string): Promise<void> {
    if (!tipoActualCodigo.value) return
    await cargarConfigCompleta(tipoActualCodigo.value, subtipoCodigo)
  }

  // ==========================================================================
  // Acciones - Umbrales
  // ==========================================================================

  /**
   * Evalua si un proyecto cumple umbral de ingreso SEIA.
   */
  async function evaluarUmbral(parametros: Record<string, number>): Promise<EvaluarUmbralResponse | null> {
    if (!tipoActualCodigo.value) return null

    try {
      const resultado = await configIndustriaService.evaluarUmbral({
        tipo_proyecto_codigo: tipoActualCodigo.value,
        parametros,
        subtipo_codigo: subtipoActualCodigo.value || undefined,
      })
      ultimaEvaluacionUmbral.value = resultado
      return resultado
    } catch (e) {
      console.error('Error evaluando umbral:', e)
      return null
    }
  }

  // ==========================================================================
  // Acciones - PAS
  // ==========================================================================

  /**
   * Identifica los PAS aplicables segun caracteristicas.
   */
  async function identificarPASAplicables(
    caracteristicas: Record<string, unknown>
  ): Promise<PASAplicable[]> {
    if (!tipoActualCodigo.value) return []

    try {
      pasAplicables.value = await configIndustriaService.identificarPASAplicables(
        tipoActualCodigo.value,
        caracteristicas,
        subtipoActualCodigo.value || undefined
      )
      return pasAplicables.value
    } catch (e) {
      console.error('Error identificando PAS:', e)
      return []
    }
  }

  // ==========================================================================
  // Acciones - Preguntas
  // ==========================================================================

  /**
   * Obtiene la siguiente pregunta del arbol.
   */
  async function obtenerSiguientePregunta(): Promise<ArbolPregunta | null> {
    if (!tipoActualCodigo.value) return null

    try {
      preguntaActual.value = await configIndustriaService.obtenerSiguientePregunta(
        tipoActualCodigo.value,
        respuestasPreguntas.value,
        subtipoActualCodigo.value || undefined
      )
      return preguntaActual.value
    } catch (e) {
      console.error('Error obteniendo pregunta:', e)
      return null
    }
  }

  /**
   * Registra una respuesta a pregunta.
   */
  function registrarRespuesta(codigo: string, valor: unknown): void {
    respuestasPreguntas.value[codigo] = valor
  }

  /**
   * Calcula el progreso de preguntas.
   */
  async function calcularProgresoPreguntas(): Promise<ProgresoPreguntas | null> {
    if (!tipoActualCodigo.value) return null

    try {
      progresoPreguntas.value = await configIndustriaService.calcularProgreso(
        tipoActualCodigo.value,
        respuestasPreguntas.value,
        subtipoActualCodigo.value || undefined
      )
      return progresoPreguntas.value
    } catch (e) {
      console.error('Error calculando progreso:', e)
      return null
    }
  }

  // ==========================================================================
  // Limpiar
  // ==========================================================================

  function limpiar(): void {
    configActual.value = null
    tipoActualCodigo.value = null
    subtipoActualCodigo.value = null
    ultimaEvaluacionUmbral.value = null
    pasAplicables.value = []
    progresoPreguntas.value = null
    preguntaActual.value = null
    respuestasPreguntas.value = {}
    error.value = null
  }

  function limpiarCache(): void {
    tipos.value = []
    tiposCargados.value = false
    resumenes.value = []
    limpiar()
  }

  // ==========================================================================
  // Return
  // ==========================================================================

  return {
    // Estado
    tipos,
    tiposCargados,
    configActual,
    tipoActualCodigo,
    subtipoActualCodigo,
    resumenes,
    cargando,
    error,
    ultimaEvaluacionUmbral,
    pasAplicables,
    progresoPreguntas,
    preguntaActual,
    respuestasPreguntas,

    // Computed
    tipoActual,
    subtiposDisponibles,
    umbralesActuales,
    pasActuales,
    normativaActual,
    oaecaActuales,
    impactosActuales,
    anexosActuales,
    preguntasActuales,
    tieneConfigCargada,

    // Acciones - Tipos
    cargarTipos,
    obtenerTipo,

    // Acciones - Configuracion
    cargarConfigCompleta,
    cargarResumenes,
    seleccionarTipo,
    seleccionarSubtipo,

    // Acciones - Umbrales
    evaluarUmbral,

    // Acciones - PAS
    identificarPASAplicables,

    // Acciones - Preguntas
    obtenerSiguientePregunta,
    registrarRespuesta,
    calcularProgresoPreguntas,

    // Limpiar
    limpiar,
    limpiarCache,
  }
})
