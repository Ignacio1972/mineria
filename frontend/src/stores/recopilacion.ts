/**
 * Store Pinia para Recopilacion Guiada (Fase 3).
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { get, post } from '@/services/api'
import type {
  IniciarCapituloResponse,
  SeccionConPreguntas,
  ContenidoEIA,
  CapituloProgreso,
  ProgresoGeneralEIA,
  ValidacionConsistenciaResponse,
  InconsistenciaDetectada,
  RespuestaIndividual,
  EstadoSeccion,
} from '@/types/recopilacion'

export const useRecopilacionStore = defineStore('recopilacion', () => {
  // ==========================================================================
  // Estado
  // ==========================================================================

  const proyectoId = ref<number | null>(null)
  const capituloActual = ref<IniciarCapituloResponse | null>(null)
  const seccionActual = ref<SeccionConPreguntas | null>(null)
  const progresoGeneral = ref<ProgresoGeneralEIA | null>(null)
  const inconsistencias = ref<InconsistenciaDetectada[]>([])

  // Estados de carga
  const cargando = ref(false)
  const guardando = ref(false)
  const validando = ref(false)
  const error = ref<string | null>(null)

  // Respuestas locales (para guardar en batch)
  const respuestasLocales = ref<Record<string, unknown>>({})

  // ==========================================================================
  // Computed
  // ==========================================================================

  const tieneCapitulo = computed(() => capituloActual.value !== null)

  const secciones = computed(() => capituloActual.value?.secciones ?? [])

  const tituloCapitulo = computed(() => capituloActual.value?.titulo ?? '')

  const numeroCapitulo = computed(() => capituloActual.value?.capitulo_numero ?? 0)

  const totalPreguntas = computed(() => capituloActual.value?.total_preguntas ?? 0)

  const preguntasObligatorias = computed(
    () => capituloActual.value?.preguntas_obligatorias ?? 0
  )

  const progresoCapituloActual = computed(() => {
    if (!secciones.value.length) return 0
    const completadas = secciones.value.filter(
      (s) => s.estado === 'completado'
    ).length
    return Math.round((completadas / secciones.value.length) * 100)
  })

  const seccionesCompletadas = computed(() =>
    secciones.value.filter((s) => s.estado === 'completado').length
  )

  const seccionesEnProgreso = computed(() =>
    secciones.value.filter((s) => s.estado === 'en_progreso').length
  )

  const capitulos = computed(() => progresoGeneral.value?.capitulos ?? [])

  const progresoTotal = computed(() => progresoGeneral.value?.progreso_general ?? 0)

  const totalInconsistencias = computed(
    () => progresoGeneral.value?.total_inconsistencias ?? 0
  )

  const hayInconsistenciasError = computed(() =>
    inconsistencias.value.some((i) => i.severidad === 'error')
  )

  const hayRespuestasPendientes = computed(
    () => Object.keys(respuestasLocales.value).length > 0
  )

  // ==========================================================================
  // Acciones - Cargar
  // ==========================================================================

  /**
   * Iniciar o retomar un capitulo.
   */
  async function iniciarCapitulo(
    idProyecto: number,
    capituloNum: number
  ): Promise<IniciarCapituloResponse | null> {
    cargando.value = true
    error.value = null
    proyectoId.value = idProyecto

    try {
      capituloActual.value = await post<IniciarCapituloResponse>(
        `/recopilacion/${idProyecto}/capitulo/${capituloNum}/iniciar`
      )

      // Seleccionar primera seccion
      if (capituloActual.value && capituloActual.value.secciones.length > 0) {
        seccionActual.value = capituloActual.value.secciones[0] ?? null
      }

      // Limpiar respuestas locales
      respuestasLocales.value = {}

      return capituloActual.value
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error cargando capitulo'
      throw e
    } finally {
      cargando.value = false
    }
  }

  /**
   * Cargar progreso general del EIA.
   */
  async function cargarProgreso(idProyecto: number): Promise<ProgresoGeneralEIA | null> {
    cargando.value = true
    error.value = null
    proyectoId.value = idProyecto

    try {
      progresoGeneral.value = await get<ProgresoGeneralEIA>(
        `/recopilacion/${idProyecto}/progreso`
      )
      return progresoGeneral.value
    } catch (e) {
      // 404 significa que no hay progreso aun
      if ((e as { status_code?: number }).status_code === 404) {
        progresoGeneral.value = null
        return null
      }
      error.value = e instanceof Error ? e.message : 'Error cargando progreso'
      throw e
    } finally {
      cargando.value = false
    }
  }

  /**
   * Cargar progreso de un capitulo especifico.
   */
  async function cargarProgresoCapitulo(
    idProyecto: number,
    capituloNum: number
  ): Promise<CapituloProgreso | null> {
    try {
      return await get<CapituloProgreso>(
        `/recopilacion/${idProyecto}/progreso/${capituloNum}`
      )
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error cargando progreso'
      throw e
    }
  }

  // ==========================================================================
  // Acciones - Guardar
  // ==========================================================================

  /**
   * Actualizar respuesta local (sin guardar en servidor).
   */
  function actualizarRespuestaLocal(codigoPregunta: string, valor: unknown): void {
    respuestasLocales.value[codigoPregunta] = valor

    // Actualizar tambien en la seccion actual para reflejar visualmente
    if (seccionActual.value) {
      const pregunta = seccionActual.value.preguntas.find(
        (p) => p.codigo_pregunta === codigoPregunta
      )
      if (pregunta) {
        pregunta.respuesta_actual = valor
      }
    }
  }

  /**
   * Guardar respuestas de la seccion actual.
   */
  async function guardarRespuestas(): Promise<ContenidoEIA | null> {
    if (!proyectoId.value || !seccionActual.value || !capituloActual.value) {
      return null
    }

    if (Object.keys(respuestasLocales.value).length === 0) {
      return null
    }

    guardando.value = true
    error.value = null

    try {
      const respuestas: RespuestaIndividual[] = Object.entries(
        respuestasLocales.value
      ).map(([codigo, valor]) => ({
        codigo_pregunta: codigo,
        valor,
      }))

      const contenido = await post<ContenidoEIA>(
        `/recopilacion/${proyectoId.value}/seccion/${seccionActual.value.seccion_codigo}?capitulo=${capituloActual.value.capitulo_numero}`,
        { respuestas }
      )

      // Actualizar estado de la seccion
      if (seccionActual.value) {
        seccionActual.value.estado = contenido.estado as EstadoSeccion
        seccionActual.value.progreso = contenido.progreso
      }

      // Actualizar en la lista de secciones
      const idx = secciones.value.findIndex(
        (s) => s.seccion_codigo === seccionActual.value?.seccion_codigo
      )
      if (idx >= 0 && capituloActual.value) {
        const seccion = capituloActual.value.secciones[idx]
        if (seccion) {
          seccion.estado = contenido.estado as EstadoSeccion
          seccion.progreso = contenido.progreso
        }
      }

      // Limpiar respuestas locales
      respuestasLocales.value = {}

      return contenido
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error guardando respuestas'
      throw e
    } finally {
      guardando.value = false
    }
  }

  // ==========================================================================
  // Acciones - Navegacion
  // ==========================================================================

  /**
   * Seleccionar una seccion.
   */
  async function seleccionarSeccion(seccionCodigo: string): Promise<void> {
    // Guardar respuestas pendientes antes de cambiar
    if (hayRespuestasPendientes.value) {
      await guardarRespuestas()
    }

    const seccion = secciones.value.find((s) => s.seccion_codigo === seccionCodigo)
    if (seccion) {
      seccionActual.value = seccion ?? null
      respuestasLocales.value = {}
    }
  }

  /**
   * Ir a la siguiente seccion.
   */
  async function siguienteSeccion(): Promise<boolean> {
    if (!seccionActual.value) return false

    const idx = secciones.value.findIndex(
      (s) => s.seccion_codigo === seccionActual.value?.seccion_codigo
    )

    const siguiente = secciones.value[idx + 1]
    if (idx >= 0 && idx < secciones.value.length - 1 && siguiente) {
      await seleccionarSeccion(siguiente.seccion_codigo)
      return true
    }

    return false
  }

  /**
   * Ir a la seccion anterior.
   */
  async function seccionAnterior(): Promise<boolean> {
    if (!seccionActual.value) return false

    const idx = secciones.value.findIndex(
      (s) => s.seccion_codigo === seccionActual.value?.seccion_codigo
    )

    const anterior = secciones.value[idx - 1]
    if (idx > 0 && anterior) {
      await seleccionarSeccion(anterior.seccion_codigo)
      return true
    }

    return false
  }

  // ==========================================================================
  // Acciones - Validacion
  // ==========================================================================

  /**
   * Validar consistencia del EIA.
   */
  async function validarConsistencia(
    idProyecto?: number
  ): Promise<ValidacionConsistenciaResponse | null> {
    const id = idProyecto ?? proyectoId.value
    if (!id) return null

    validando.value = true
    error.value = null

    try {
      const resultado = await post<ValidacionConsistenciaResponse>(
        `/recopilacion/${id}/validar`
      )

      inconsistencias.value = resultado.inconsistencias

      return resultado
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error validando consistencia'
      throw e
    } finally {
      validando.value = false
    }
  }

  /**
   * Obtener inconsistencias sin re-evaluar.
   */
  async function obtenerInconsistencias(
    idProyecto?: number
  ): Promise<InconsistenciaDetectada[]> {
    const id = idProyecto ?? proyectoId.value
    if (!id) return []

    try {
      const resultado = await get<ValidacionConsistenciaResponse>(
        `/recopilacion/${id}/inconsistencias`
      )

      inconsistencias.value = resultado.inconsistencias
      return inconsistencias.value
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error obteniendo inconsistencias'
      return []
    }
  }

  // ==========================================================================
  // Helpers
  // ==========================================================================

  /**
   * Obtener una seccion por codigo.
   */
  function getSeccion(codigo: string): SeccionConPreguntas | undefined {
    return secciones.value.find((s) => s.seccion_codigo === codigo)
  }

  /**
   * Obtener un capitulo del progreso general.
   */
  function getCapituloProgreso(numero: number): CapituloProgreso | undefined {
    return capitulos.value.find((c) => c.numero === numero)
  }

  /**
   * Verificar si hay respuesta para una pregunta.
   */
  function tieneRespuesta(codigoPregunta: string): boolean {
    // Primero verificar en respuestas locales
    if (respuestasLocales.value[codigoPregunta] !== undefined) {
      return respuestasLocales.value[codigoPregunta] !== null &&
        respuestasLocales.value[codigoPregunta] !== ''
    }

    // Luego verificar en la seccion actual
    if (seccionActual.value) {
      const pregunta = seccionActual.value.preguntas.find(
        (p) => p.codigo_pregunta === codigoPregunta
      )
      return pregunta?.respuesta_actual !== null &&
        pregunta?.respuesta_actual !== undefined &&
        pregunta?.respuesta_actual !== ''
    }

    return false
  }

  // ==========================================================================
  // Limpiar
  // ==========================================================================

  function limpiar(): void {
    proyectoId.value = null
    capituloActual.value = null
    seccionActual.value = null
    progresoGeneral.value = null
    inconsistencias.value = []
    respuestasLocales.value = {}
    error.value = null
  }

  // ==========================================================================
  // Return
  // ==========================================================================

  return {
    // Estado
    proyectoId,
    capituloActual,
    seccionActual,
    progresoGeneral,
    inconsistencias,
    respuestasLocales,
    cargando,
    guardando,
    validando,
    error,

    // Computed
    tieneCapitulo,
    secciones,
    tituloCapitulo,
    numeroCapitulo,
    totalPreguntas,
    preguntasObligatorias,
    progresoCapituloActual,
    seccionesCompletadas,
    seccionesEnProgreso,
    capitulos,
    progresoTotal,
    totalInconsistencias,
    hayInconsistenciasError,
    hayRespuestasPendientes,

    // Acciones
    iniciarCapitulo,
    cargarProgreso,
    cargarProgresoCapitulo,
    actualizarRespuestaLocal,
    guardarRespuestas,
    seleccionarSeccion,
    siguienteSeccion,
    seccionAnterior,
    validarConsistencia,
    obtenerInconsistencias,

    // Helpers
    getSeccion,
    getCapituloProgreso,
    tieneRespuesta,

    // Limpiar
    limpiar,
  }
})
