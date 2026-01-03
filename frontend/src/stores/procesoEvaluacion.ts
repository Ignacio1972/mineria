/**
 * Store Pinia para Gestor de Proceso de Evaluacion SEIA (ICSARA/Adendas).
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { get, post, put } from '@/services/api'
import type {
  ProcesoEvaluacion,
  ResumenProcesoEvaluacion,
  PlazoEvaluacion,
  TimelineEvaluacion,
  ICSARA,
  Adenda,
  EstadisticasICSARA,
  ObservacionICSARA,
  ICSARACreate,
  AdendaCreate,
  IniciarProcesoRequest,
  RegistrarAdmisibilidadRequest,
  RegistrarRCARequest,
  ActualizarEstadoObservacionRequest,
  EstadoEvaluacion,
} from '@/types/procesoEvaluacion'

const API_BASE = '/api/v1/proceso-evaluacion'

export const useProcesoEvaluacionStore = defineStore('procesoEvaluacion', () => {
  // ==========================================================================
  // Estado
  // ==========================================================================

  const proyectoId = ref<number | null>(null)
  const proceso = ref<ProcesoEvaluacion | null>(null)
  const resumen = ref<ResumenProcesoEvaluacion | null>(null)
  const plazos = ref<PlazoEvaluacion | null>(null)
  const timeline = ref<TimelineEvaluacion | null>(null)
  const estadisticas = ref<EstadisticasICSARA | null>(null)

  const cargando = ref(false)
  const guardando = ref(false)
  const error = ref<string | null>(null)

  // ==========================================================================
  // Computed - Estado General
  // ==========================================================================

  const tieneProceso = computed(() => proceso.value !== null)

  const estadoActual = computed<EstadoEvaluacion>(() =>
    proceso.value?.estado_evaluacion ?? 'no_ingresado'
  )

  const estadoLabel = computed(() => resumen.value?.estado_label ?? 'No ingresado')

  const porcentajePlazo = computed(() =>
    proceso.value?.porcentaje_plazo ?? 0
  )

  const diasRestantes = computed(() =>
    proceso.value?.dias_restantes ?? 0
  )

  const diasTranscurridos = computed(() =>
    proceso.value?.dias_transcurridos ?? 0
  )

  // ==========================================================================
  // Computed - ICSARA
  // ==========================================================================

  const icsaras = computed<ICSARA[]>(() =>
    proceso.value?.icsaras ?? []
  )

  const totalIcsara = computed(() =>
    proceso.value?.total_icsara ?? 0
  )

  const icsaraActual = computed<ICSARA | null>(() => {
    if (!icsaras.value.length) return null
    return icsaras.value.reduce((max, i) =>
      i.numero_icsara > max.numero_icsara ? i : max
    )
  })

  const totalObservaciones = computed(() =>
    proceso.value?.total_observaciones ?? 0
  )

  const observacionesPendientes = computed(() =>
    proceso.value?.observaciones_pendientes ?? 0
  )

  const observacionesResueltas = computed(() =>
    totalObservaciones.value - observacionesPendientes.value
  )

  const porcentajeObservacionesResueltas = computed(() => {
    if (!totalObservaciones.value) return 0
    return Math.round((observacionesResueltas.value / totalObservaciones.value) * 100)
  })

  // Todas las observaciones de todos los ICSARA
  const todasLasObservaciones = computed<ObservacionICSARA[]>(() => {
    const obs: ObservacionICSARA[] = []
    for (const icsara of icsaras.value) {
      obs.push(...(icsara.observaciones || []))
    }
    return obs
  })

  // Observaciones agrupadas por organismo
  const observacionesPorOAECA = computed<Record<string, number>>(() =>
    resumen.value?.observaciones_por_oaeca ?? {}
  )

  // Organismos con mas observaciones
  const oaecaCriticos = computed<string[]>(() =>
    resumen.value?.oaeca_criticos ?? []
  )

  // ==========================================================================
  // Computed - Adendas
  // ==========================================================================

  const totalAdendas = computed(() => {
    let count = 0
    for (const icsara of icsaras.value) {
      count += (icsara.adendas || []).length
    }
    return count
  })

  const ultimaAdenda = computed<Adenda | null>(() => {
    let ultima: Adenda | null = null
    for (const icsara of icsaras.value) {
      for (const adenda of (icsara.adendas || [])) {
        if (!ultima || adenda.fecha_presentacion > ultima.fecha_presentacion) {
          ultima = adenda
        }
      }
    }
    return ultima
  })

  // ==========================================================================
  // Computed - Alertas y Proxima Accion
  // ==========================================================================

  const proximaAccion = computed(() =>
    resumen.value?.proxima_accion ?? 'Sin accion definida'
  )

  const fechaLimite = computed(() =>
    resumen.value?.fecha_limite ?? null
  )

  const alerta = computed(() =>
    resumen.value?.alerta ?? null
  )

  const estadoPlazo = computed(() =>
    plazos.value?.estado_plazo ?? 'normal'
  )

  const tieneAlerta = computed(() => alerta.value !== null)

  // ==========================================================================
  // Computed - RCA
  // ==========================================================================

  const tieneRCA = computed(() =>
    proceso.value?.fecha_rca !== null
  )

  const resultadoRCA = computed(() =>
    proceso.value?.resultado_rca ?? null
  )

  const numeroRCA = computed(() =>
    proceso.value?.numero_rca ?? null
  )

  const condicionesRCA = computed(() =>
    proceso.value?.condiciones_rca ?? []
  )

  // ==========================================================================
  // Acciones - Cargar Datos
  // ==========================================================================

  async function cargarProceso(id: number): Promise<void> {
    proyectoId.value = id
    cargando.value = true
    error.value = null

    try {
      const [procesoData, resumenData, plazosData, timelineData] = await Promise.all([
        get<ProcesoEvaluacion>(`${API_BASE}/${id}`).catch(() => null),
        get<ResumenProcesoEvaluacion>(`${API_BASE}/${id}/resumen`).catch(() => null),
        get<PlazoEvaluacion>(`${API_BASE}/${id}/plazos`).catch(() => null),
        get<TimelineEvaluacion>(`${API_BASE}/${id}/timeline`).catch(() => null),
      ])

      proceso.value = procesoData
      resumen.value = resumenData
      plazos.value = plazosData
      timeline.value = timelineData
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error al cargar proceso'
      console.error('Error cargando proceso de evaluacion:', e)
    } finally {
      cargando.value = false
    }
  }

  async function cargarEstadisticas(): Promise<void> {
    if (!proyectoId.value) return

    try {
      estadisticas.value = await get<EstadisticasICSARA>(
        `${API_BASE}/${proyectoId.value}/estadisticas-icsara`
      )
    } catch (e) {
      console.error('Error cargando estadisticas:', e)
    }
  }

  async function refrescar(): Promise<void> {
    if (proyectoId.value) {
      await cargarProceso(proyectoId.value)
    }
  }

  // ==========================================================================
  // Acciones - Proceso de Evaluacion
  // ==========================================================================

  async function iniciarProceso(datos: IniciarProcesoRequest): Promise<boolean> {
    if (!proyectoId.value) return false

    guardando.value = true
    error.value = null

    try {
      const params = new URLSearchParams({
        fecha_ingreso: datos.fecha_ingreso,
        instrumento: datos.instrumento,
      })

      proceso.value = await post<ProcesoEvaluacion>(
        `${API_BASE}/${proyectoId.value}/iniciar?${params}`
      )
      await refrescar()
      return true
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error al iniciar proceso'
      return false
    } finally {
      guardando.value = false
    }
  }

  async function registrarAdmisibilidad(
    datos: RegistrarAdmisibilidadRequest
  ): Promise<boolean> {
    if (!proyectoId.value) return false

    guardando.value = true
    error.value = null

    try {
      proceso.value = await post<ProcesoEvaluacion>(
        `${API_BASE}/${proyectoId.value}/admisibilidad`,
        datos
      )
      await refrescar()
      return true
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error al registrar admisibilidad'
      return false
    } finally {
      guardando.value = false
    }
  }

  // ==========================================================================
  // Acciones - ICSARA
  // ==========================================================================

  async function registrarICSARA(datos: ICSARACreate): Promise<ICSARA | null> {
    if (!proyectoId.value) return null

    guardando.value = true
    error.value = null

    try {
      const icsara = await post<ICSARA>(
        `${API_BASE}/${proyectoId.value}/icsara`,
        datos
      )
      await refrescar()
      return icsara
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error al registrar ICSARA'
      return null
    } finally {
      guardando.value = false
    }
  }

  async function actualizarEstadoObservacion(
    icsaraId: number,
    observacionId: string,
    datos: ActualizarEstadoObservacionRequest
  ): Promise<boolean> {
    if (!proyectoId.value) return false

    guardando.value = true
    error.value = null

    try {
      await put<ICSARA>(
        `${API_BASE}/${proyectoId.value}/icsara/${icsaraId}/observacion/${observacionId}`,
        datos
      )
      await refrescar()
      return true
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error al actualizar observacion'
      return false
    } finally {
      guardando.value = false
    }
  }

  // ==========================================================================
  // Acciones - Adenda
  // ==========================================================================

  async function registrarAdenda(
    icsaraId: number,
    datos: AdendaCreate
  ): Promise<Adenda | null> {
    if (!proyectoId.value) return null

    guardando.value = true
    error.value = null

    try {
      const adenda = await post<Adenda>(
        `${API_BASE}/${proyectoId.value}/icsara/${icsaraId}/adenda`,
        datos
      )
      await refrescar()
      return adenda
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error al registrar Adenda'
      return null
    } finally {
      guardando.value = false
    }
  }

  // ==========================================================================
  // Acciones - RCA
  // ==========================================================================

  async function registrarRCA(datos: RegistrarRCARequest): Promise<boolean> {
    if (!proyectoId.value) return false

    guardando.value = true
    error.value = null

    try {
      proceso.value = await post<ProcesoEvaluacion>(
        `${API_BASE}/${proyectoId.value}/rca`,
        datos
      )
      await refrescar()
      return true
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error al registrar RCA'
      return false
    } finally {
      guardando.value = false
    }
  }

  // ==========================================================================
  // Helpers
  // ==========================================================================

  function obtenerICSARA(numero: number): ICSARA | null {
    return icsaras.value.find(i => i.numero_icsara === numero) ?? null
  }

  function obtenerObservacion(icsaraNumero: number, obsId: string): ObservacionICSARA | null {
    const icsara = obtenerICSARA(icsaraNumero)
    if (!icsara) return null
    return icsara.observaciones.find(o => o.id === obsId) ?? null
  }

  function limpiar(): void {
    proyectoId.value = null
    proceso.value = null
    resumen.value = null
    plazos.value = null
    timeline.value = null
    estadisticas.value = null
    error.value = null
  }

  // ==========================================================================
  // Return
  // ==========================================================================

  return {
    // Estado
    proyectoId,
    proceso,
    resumen,
    plazos,
    timeline,
    estadisticas,
    cargando,
    guardando,
    error,

    // Computed - General
    tieneProceso,
    estadoActual,
    estadoLabel,
    porcentajePlazo,
    diasRestantes,
    diasTranscurridos,

    // Computed - ICSARA
    icsaras,
    totalIcsara,
    icsaraActual,
    totalObservaciones,
    observacionesPendientes,
    observacionesResueltas,
    porcentajeObservacionesResueltas,
    todasLasObservaciones,
    observacionesPorOAECA,
    oaecaCriticos,

    // Computed - Adendas
    totalAdendas,
    ultimaAdenda,

    // Computed - Alertas
    proximaAccion,
    fechaLimite,
    alerta,
    estadoPlazo,
    tieneAlerta,

    // Computed - RCA
    tieneRCA,
    resultadoRCA,
    numeroRCA,
    condicionesRCA,

    // Acciones
    cargarProceso,
    cargarEstadisticas,
    refrescar,
    iniciarProceso,
    registrarAdmisibilidad,
    registrarICSARA,
    actualizarEstadoObservacion,
    registrarAdenda,
    registrarRCA,

    // Helpers
    obtenerICSARA,
    obtenerObservacion,
    limpiar,
  }
})
