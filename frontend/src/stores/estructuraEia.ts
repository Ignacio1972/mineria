/**
 * Store Pinia para Estructura EIA (Fase 2).
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { get, post, patch } from '@/services/api'
import type {
  EstructuraEIA,
  CapituloConEstado,
  PASConEstado,
  AnexoRequerido,
  ComponenteLineaBaseEnPlan,
  EstimacionComplejidad,
  ActualizarCapituloRequest,
  ActualizarPASRequest,
  ActualizarAnexoRequest,
} from '@/types'

export const useEstructuraEiaStore = defineStore('estructuraEia', () => {
  // ==========================================================================
  // Estado
  // ==========================================================================

  const proyectoId = ref<number | null>(null)
  const estructura = ref<EstructuraEIA | null>(null)
  const cargando = ref(false)
  const generando = ref(false)
  const guardando = ref(false)
  const error = ref<string | null>(null)

  // ==========================================================================
  // Computed
  // ==========================================================================

  const tieneEstructura = computed(() => estructura.value !== null)

  const capitulos = computed<CapituloConEstado[]>(() =>
    estructura.value?.capitulos ?? []
  )

  const pasRequeridos = computed<PASConEstado[]>(() =>
    estructura.value?.pas_requeridos ?? []
  )

  const anexos = computed<AnexoRequerido[]>(() =>
    estructura.value?.anexos_requeridos ?? []
  )

  const planLineaBase = computed<ComponenteLineaBaseEnPlan[]>(() =>
    estructura.value?.plan_linea_base ?? []
  )

  const estimacion = computed<EstimacionComplejidad | null>(() =>
    estructura.value?.estimacion_complejidad ?? null
  )

  const progresoGeneral = computed(() => {
    if (!capitulos.value.length) return 0
    const completados = capitulos.value.filter(c => c.estado === 'completado').length
    return Math.round((completados / capitulos.value.length) * 100)
  })

  const capitulosCompletados = computed(() =>
    capitulos.value.filter(c => c.estado === 'completado').length
  )

  const capitulosEnProgreso = computed(() =>
    capitulos.value.filter(c => c.estado === 'en_progreso').length
  )

  const capitulosPendientes = computed(() =>
    capitulos.value.filter(c => c.estado === 'pendiente').length
  )

  const pasAprobados = computed(() =>
    pasRequeridos.value.filter(p => p.estado === 'aprobado').length
  )

  const pasEnTramite = computed(() =>
    pasRequeridos.value.filter(p => p.estado === 'en_tramite').length
  )

  const pasPendientes = computed(() =>
    pasRequeridos.value.filter(p =>
      p.estado === 'identificado' || p.estado === 'requerido'
    ).length
  )

  const anexosCompletados = computed(() =>
    anexos.value.filter(a => a.estado === 'completado').length
  )

  const anexosEnElaboracion = computed(() =>
    anexos.value.filter(a => a.estado === 'en_elaboracion').length
  )

  const duracionTotalLineaBase = computed(() =>
    planLineaBase.value.reduce((acc, c) => acc + (c.duracion_estimada_dias || 0), 0)
  )

  const nivelComplejidad = computed(() =>
    estimacion.value?.nivel ?? null
  )

  const tiempoEstimadoMeses = computed(() =>
    estimacion.value?.tiempo_estimado_meses ?? null
  )

  // ==========================================================================
  // Acciones - Cargar
  // ==========================================================================

  /**
   * Carga la estructura EIA del proyecto.
   */
  async function cargarEstructura(id: number): Promise<EstructuraEIA | null> {
    cargando.value = true
    error.value = null
    proyectoId.value = id

    try {
      estructura.value = await get<EstructuraEIA>(
        `/estructura-eia/proyecto/${id}`
      )
      return estructura.value
    } catch (e) {
      // 404 significa que no hay estructura aun
      if ((e as { status_code?: number }).status_code === 404) {
        estructura.value = null
        return null
      }
      error.value = e instanceof Error ? e.message : 'Error cargando estructura'
      throw e
    } finally {
      cargando.value = false
    }
  }

  /**
   * Recarga la estructura actual.
   */
  async function recargarEstructura(): Promise<void> {
    if (proyectoId.value) {
      await cargarEstructura(proyectoId.value)
    }
  }

  // ==========================================================================
  // Acciones - Generar
  // ==========================================================================

  /**
   * Genera la estructura EIA para un proyecto.
   */
  async function generarEstructura(
    id: number,
    forzarRegenerar: boolean = false
  ): Promise<EstructuraEIA | null> {
    generando.value = true
    error.value = null
    proyectoId.value = id

    try {
      estructura.value = await post<EstructuraEIA>(
        `/estructura-eia/generar/${id}`,
        { forzar_regenerar: forzarRegenerar }
      )
      return estructura.value
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error generando estructura'
      throw e
    } finally {
      generando.value = false
    }
  }

  // ==========================================================================
  // Acciones - Actualizar Capitulos
  // ==========================================================================

  /**
   * Actualiza el estado de un capitulo.
   */
  async function actualizarCapitulo(
    numero: number,
    data: ActualizarCapituloRequest
  ): Promise<void> {
    if (!proyectoId.value) return

    guardando.value = true
    try {
      await patch(
        `/estructura-eia/proyecto/${proyectoId.value}/capitulo/${numero}`,
        data
      )

      // Actualizar localmente
      const capitulo = capitulos.value.find(c => c.numero === numero)
      if (capitulo) {
        capitulo.estado = data.estado
        if (data.progreso_porcentaje !== undefined) {
          capitulo.progreso_porcentaje = data.progreso_porcentaje
        }
        if (data.notas !== undefined) {
          capitulo.notas = data.notas
        }
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error actualizando capitulo'
      throw e
    } finally {
      guardando.value = false
    }
  }

  // ==========================================================================
  // Acciones - Actualizar PAS
  // ==========================================================================

  /**
   * Actualiza el estado de un PAS.
   */
  async function actualizarPAS(
    articulo: number,
    data: ActualizarPASRequest
  ): Promise<void> {
    if (!proyectoId.value) return

    guardando.value = true
    try {
      await patch(
        `/estructura-eia/proyecto/${proyectoId.value}/pas/${articulo}`,
        data
      )

      // Actualizar localmente
      const pas = pasRequeridos.value.find(p => p.articulo === articulo)
      if (pas) {
        pas.estado = data.estado
        if (data.fecha_limite !== undefined) {
          pas.fecha_limite = data.fecha_limite
        }
        if (data.notas !== undefined) {
          pas.notas = data.notas
        }
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error actualizando PAS'
      throw e
    } finally {
      guardando.value = false
    }
  }

  // ==========================================================================
  // Acciones - Actualizar Anexos
  // ==========================================================================

  /**
   * Actualiza el estado de un anexo.
   */
  async function actualizarAnexo(
    codigo: string,
    data: ActualizarAnexoRequest
  ): Promise<void> {
    if (!proyectoId.value) return

    guardando.value = true
    try {
      await patch(
        `/estructura-eia/proyecto/${proyectoId.value}/anexo/${codigo}`,
        data
      )

      // Actualizar localmente
      const anexo = anexos.value.find(a => a.codigo === codigo)
      if (anexo) {
        anexo.estado = data.estado
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error actualizando anexo'
      throw e
    } finally {
      guardando.value = false
    }
  }

  // ==========================================================================
  // Helpers
  // ==========================================================================

  /**
   * Obtiene un capitulo por numero.
   */
  function getCapitulo(numero: number): CapituloConEstado | undefined {
    return capitulos.value.find(c => c.numero === numero)
  }

  /**
   * Obtiene un PAS por articulo.
   */
  function getPAS(articulo: number): PASConEstado | undefined {
    return pasRequeridos.value.find(p => p.articulo === articulo)
  }

  /**
   * Obtiene un anexo por codigo.
   */
  function getAnexo(codigo: string): AnexoRequerido | undefined {
    return anexos.value.find(a => a.codigo === codigo)
  }

  /**
   * Obtiene componentes de linea base obligatorios.
   */
  function getComponentesObligatorios(): ComponenteLineaBaseEnPlan[] {
    return planLineaBase.value.filter(c => c.es_obligatorio)
  }

  /**
   * Obtiene PAS obligatorios.
   */
  function getPASObligatorios(): PASConEstado[] {
    return pasRequeridos.value.filter(p => p.obligatoriedad === 'obligatorio')
  }

  // ==========================================================================
  // Limpiar
  // ==========================================================================

  function limpiar(): void {
    proyectoId.value = null
    estructura.value = null
    error.value = null
  }

  // ==========================================================================
  // Return
  // ==========================================================================

  return {
    // Estado
    proyectoId,
    estructura,
    cargando,
    generando,
    guardando,
    error,

    // Computed
    tieneEstructura,
    capitulos,
    pasRequeridos,
    anexos,
    planLineaBase,
    estimacion,
    progresoGeneral,
    capitulosCompletados,
    capitulosEnProgreso,
    capitulosPendientes,
    pasAprobados,
    pasEnTramite,
    pasPendientes,
    anexosCompletados,
    anexosEnElaboracion,
    duracionTotalLineaBase,
    nivelComplejidad,
    tiempoEstimadoMeses,

    // Acciones
    cargarEstructura,
    recargarEstructura,
    generarEstructura,
    actualizarCapitulo,
    actualizarPAS,
    actualizarAnexo,

    // Helpers
    getCapitulo,
    getPAS,
    getAnexo,
    getComponentesObligatorios,
    getPASObligatorios,

    // Limpiar
    limpiar,
  }
})
