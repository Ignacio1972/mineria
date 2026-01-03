/**
 * Store Pinia para Generación de EIA (Fase 4).
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { get, post, patch } from '@/services/api'
import type {
  DocumentoEIA,
  DocumentoCompletoResponse,
  DocumentoEIAUpdate,
  VersionEIA,
  CrearVersionRequest,
  ContenidoCapitulo,
  GeneracionResponse,
  ProgresoGeneracion,
  ResultadoValidacion,
  ObservacionValidacion,
  ExportacionEIA,
  EstadisticasDocumento,
  SeveridadValidacion,
  FormatoExportacionEIA,
} from '@/types/generacionEia'

export const useGeneracionEiaStore = defineStore('generacionEia', () => {
  // ==========================================================================
  // Estado
  // ==========================================================================

  const proyectoId = ref<number | null>(null)
  const documento = ref<DocumentoEIA | null>(null)
  const versiones = ref<VersionEIA[]>([])
  const exportaciones = ref<ExportacionEIA[]>([])
  const observaciones = ref<ObservacionValidacion[]>([])
  const progreso = ref<ProgresoGeneracion[]>([])
  const estadisticas = ref<EstadisticasDocumento | null>(null)

  // Estados de carga
  const cargando = ref(false)
  const compilando = ref(false)
  const generandoCapitulo = ref<number | null>(null)
  const validando = ref(false)
  const exportando = ref(false)
  const guardando = ref(false)
  const error = ref<string | null>(null)

  // Editor
  const capituloEditando = ref<number | null>(null)
  const contenidoSinGuardar = ref(false)

  // ==========================================================================
  // Computed
  // ==========================================================================

  const tieneDocumento = computed(() => documento.value !== null)

  const contenidoCapitulos = computed<Record<string, ContenidoCapitulo>>(() =>
    (documento.value?.contenido_capitulos as Record<string, ContenidoCapitulo>) ?? {}
  )

  const capituloActual = computed<ContenidoCapitulo | null>(() => {
    if (!capituloEditando.value || !contenidoCapitulos.value) return null
    return contenidoCapitulos.value[capituloEditando.value.toString()] ?? null
  })

  const capitulosGenerados = computed(() =>
    Object.keys(contenidoCapitulos.value).map(k => parseInt(k))
  )

  const totalPalabras = computed(() =>
    estadisticas.value?.total_palabras ?? 0
  )

  const porcentajeCompletitud = computed(() =>
    estadisticas.value?.porcentaje_completitud ?? 0
  )

  const observacionesPendientes = computed(() =>
    observaciones.value.filter(o => o.estado === 'pendiente')
  )

  const observacionesError = computed(() =>
    observaciones.value.filter(o => o.severidad === 'error' && o.estado === 'pendiente')
  )

  const observacionesWarning = computed(() =>
    observaciones.value.filter(o => o.severidad === 'warning' && o.estado === 'pendiente')
  )

  const esValido = computed(() =>
    observacionesError.value.length === 0
  )

  const ultimaVersion = computed(() => {
    if (versiones.value.length === 0) return null
    return versiones.value.reduce((max, v) => v.version > max.version ? v : max, versiones.value[0]!)
  })

  const ultimaExportacion = computed(() => {
    if (exportaciones.value.length === 0) return null
    return exportaciones.value.reduce((max, e) =>
      new Date(e.created_at) > new Date(max.created_at) ? e : max,
      exportaciones.value[0]!
    )
  })

  // ==========================================================================
  // Acciones - Cargar Documento
  // ==========================================================================

  /**
   * Carga el documento EIA completo con todas sus relaciones.
   */
  async function cargarDocumentoCompleto(id: number): Promise<DocumentoCompletoResponse | null> {
    cargando.value = true
    error.value = null
    proyectoId.value = id

    try {
      const response = await get<DocumentoCompletoResponse>(
        `/generacion/${id}/documento/completo`
      )

      documento.value = response.documento
      versiones.value = response.versiones
      exportaciones.value = response.exportaciones
      observaciones.value = response.observaciones_pendientes
      estadisticas.value = response.estadisticas
      progreso.value = response.progreso_capitulos

      return response
    } catch (e) {
      // 404 significa que no hay documento aún
      if ((e as { status_code?: number }).status_code === 404) {
        limpiar()
        proyectoId.value = id
        return null
      }
      error.value = e instanceof Error ? e.message : 'Error cargando documento'
      throw e
    } finally {
      cargando.value = false
    }
  }

  /**
   * Carga solo el documento básico.
   */
  async function cargarDocumento(id: number, version?: number): Promise<DocumentoEIA | null> {
    cargando.value = true
    error.value = null
    proyectoId.value = id

    try {
      const url = version
        ? `/generacion/${id}/documento?version=${version}`
        : `/generacion/${id}/documento`
      documento.value = await get<DocumentoEIA>(url)
      return documento.value
    } catch (e) {
      if ((e as { status_code?: number }).status_code === 404) {
        documento.value = null
        return null
      }
      error.value = e instanceof Error ? e.message : 'Error cargando documento'
      throw e
    } finally {
      cargando.value = false
    }
  }

  /**
   * Recarga el documento actual.
   */
  async function recargarDocumento(): Promise<void> {
    if (proyectoId.value) {
      await cargarDocumentoCompleto(proyectoId.value)
    }
  }

  // ==========================================================================
  // Acciones - Compilar y Generar
  // ==========================================================================

  /**
   * Compila el documento EIA completo.
   */
  async function compilarDocumento(
    capitulos?: number[],
    regenerar: boolean = false
  ): Promise<GeneracionResponse> {
    if (!proyectoId.value) throw new Error('No hay proyecto seleccionado')

    compilando.value = true
    error.value = null

    try {
      const response = await post<GeneracionResponse>(
        `/generacion/${proyectoId.value}/compilar`,
        {
          incluir_capitulos: capitulos ?? null,
          regenerar_existentes: regenerar,
        }
      )

      // Recargar documento tras compilación
      await recargarDocumento()

      return response
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error compilando documento'
      throw e
    } finally {
      compilando.value = false
    }
  }

  /**
   * Genera un capítulo específico.
   */
  async function generarCapitulo(
    capitulo: number,
    instrucciones?: string,
    regenerar: boolean = false
  ): Promise<ContenidoCapitulo> {
    if (!proyectoId.value) throw new Error('No hay proyecto seleccionado')

    generandoCapitulo.value = capitulo
    error.value = null

    try {
      const url = instrucciones
        ? `/generacion/${proyectoId.value}/capitulo/${capitulo}?regenerar=${regenerar}&instrucciones=${encodeURIComponent(instrucciones)}`
        : `/generacion/${proyectoId.value}/capitulo/${capitulo}?regenerar=${regenerar}`

      const response = await post<ContenidoCapitulo>(url, {})

      // Actualizar contenido local
      if (documento.value) {
        if (!documento.value.contenido_capitulos) {
          documento.value.contenido_capitulos = {}
        }
        (documento.value.contenido_capitulos as Record<string, ContenidoCapitulo>)[capitulo.toString()] = response
      }

      // Actualizar progreso
      await cargarProgreso()

      return response
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error generando capítulo'
      throw e
    } finally {
      generandoCapitulo.value = null
    }
  }

  /**
   * Regenera una sección específica.
   */
  async function regenerarSeccion(
    capitulo: number,
    seccion: string,
    instrucciones: string
  ): Promise<string> {
    if (!proyectoId.value) throw new Error('No hay proyecto seleccionado')

    generandoCapitulo.value = capitulo
    error.value = null

    try {
      const response = await post<{ texto_regenerado: string }>(
        `/generacion/${proyectoId.value}/regenerar`,
        {
          capitulo_numero: capitulo,
          seccion_codigo: seccion,
          instrucciones,
        }
      )

      // Recargar documento
      await recargarDocumento()

      return response.texto_regenerado
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error regenerando sección'
      throw e
    } finally {
      generandoCapitulo.value = null
    }
  }

  // ==========================================================================
  // Acciones - Actualizar Contenido
  // ==========================================================================

  /**
   * Actualiza el contenido de un capítulo manualmente.
   */
  async function actualizarCapitulo(
    capitulo: number,
    contenido: string,
    titulo?: string
  ): Promise<ContenidoCapitulo> {
    if (!proyectoId.value) throw new Error('No hay proyecto seleccionado')

    guardando.value = true
    error.value = null

    try {
      const url = titulo
        ? `/generacion/${proyectoId.value}/capitulo/${capitulo}/contenido?contenido=${encodeURIComponent(contenido)}&titulo=${encodeURIComponent(titulo)}`
        : `/generacion/${proyectoId.value}/capitulo/${capitulo}/contenido?contenido=${encodeURIComponent(contenido)}`

      const response = await fetch(`/api/v1${url}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
      }).then(r => r.json()) as ContenidoCapitulo

      // Actualizar contenido local
      if (documento.value?.contenido_capitulos) {
        (documento.value.contenido_capitulos as Record<string, ContenidoCapitulo>)[capitulo.toString()] = response
      }

      contenidoSinGuardar.value = false

      return response
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error actualizando capítulo'
      throw e
    } finally {
      guardando.value = false
    }
  }

  /**
   * Actualiza metadatos del documento.
   */
  async function actualizarDocumento(data: DocumentoEIAUpdate): Promise<DocumentoEIA> {
    if (!proyectoId.value) throw new Error('No hay proyecto seleccionado')

    guardando.value = true
    error.value = null

    try {
      const response = await patch<DocumentoEIA>(
        `/generacion/${proyectoId.value}/documento`,
        data
      )

      documento.value = response
      return response
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error actualizando documento'
      throw e
    } finally {
      guardando.value = false
    }
  }

  // ==========================================================================
  // Acciones - Versionado
  // ==========================================================================

  /**
   * Carga las versiones del documento.
   */
  async function cargarVersiones(): Promise<VersionEIA[]> {
    if (!proyectoId.value) return []

    try {
      versiones.value = await get<VersionEIA[]>(
        `/generacion/${proyectoId.value}/versiones`
      )
      return versiones.value
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error cargando versiones'
      throw e
    }
  }

  /**
   * Crea una nueva versión (snapshot).
   */
  async function crearVersion(cambios: string, creadoPor?: string): Promise<VersionEIA> {
    if (!proyectoId.value) throw new Error('No hay proyecto seleccionado')

    guardando.value = true
    error.value = null

    try {
      const response = await post<VersionEIA>(
        `/generacion/${proyectoId.value}/version`,
        { cambios, creado_por: creadoPor } as CrearVersionRequest
      )

      versiones.value.push(response)
      return response
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error creando versión'
      throw e
    } finally {
      guardando.value = false
    }
  }

  /**
   * Restaura una versión anterior.
   */
  async function restaurarVersion(versionNum: number): Promise<DocumentoEIA> {
    if (!proyectoId.value) throw new Error('No hay proyecto seleccionado')

    guardando.value = true
    error.value = null

    try {
      const response = await post<DocumentoEIA>(
        `/generacion/${proyectoId.value}/restaurar/${versionNum}`,
        {}
      )

      documento.value = response
      await recargarDocumento()

      return response
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error restaurando versión'
      throw e
    } finally {
      guardando.value = false
    }
  }

  // ==========================================================================
  // Acciones - Validación
  // ==========================================================================

  /**
   * Valida el documento contra reglas SEA.
   */
  async function validarDocumento(
    severidadMinima: SeveridadValidacion = 'info'
  ): Promise<ResultadoValidacion> {
    if (!proyectoId.value) throw new Error('No hay proyecto seleccionado')

    validando.value = true
    error.value = null

    try {
      const response = await post<ResultadoValidacion>(
        `/generacion/${proyectoId.value}/validar?nivel_severidad=${severidadMinima}`,
        {}
      )

      observaciones.value = response.observaciones
      return response
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error validando documento'
      throw e
    } finally {
      validando.value = false
    }
  }

  /**
   * Carga las validaciones existentes.
   */
  async function cargarValidaciones(): Promise<ResultadoValidacion> {
    if (!proyectoId.value) throw new Error('No hay proyecto seleccionado')

    try {
      const response = await get<ResultadoValidacion>(
        `/generacion/${proyectoId.value}/validaciones`
      )

      observaciones.value = response.observaciones
      return response
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error cargando validaciones'
      throw e
    }
  }

  // ==========================================================================
  // Acciones - Exportación
  // ==========================================================================

  /**
   * Exporta el documento a un formato específico.
   */
  async function exportarDocumento(
    formato: FormatoExportacionEIA,
    configuracion?: Record<string, unknown>
  ): Promise<ExportacionEIA> {
    if (!proyectoId.value) throw new Error('No hay proyecto seleccionado')

    exportando.value = true
    error.value = null

    try {
      const response = await post<ExportacionEIA>(
        `/generacion/${proyectoId.value}/exportar/${formato}`,
        configuracion ? { configuracion } : {}
      )

      exportaciones.value.push(response)
      return response
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error exportando documento'
      throw e
    } finally {
      exportando.value = false
    }
  }

  /**
   * Carga las exportaciones realizadas.
   */
  async function cargarExportaciones(): Promise<ExportacionEIA[]> {
    if (!proyectoId.value) return []

    try {
      exportaciones.value = await get<ExportacionEIA[]>(
        `/generacion/${proyectoId.value}/exports`
      )
      return exportaciones.value
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error cargando exportaciones'
      throw e
    }
  }

  /**
   * Obtiene la URL de descarga de una exportación.
   */
  function getUrlDescarga(exportacionId: number): string {
    return `/api/v1/generacion/${proyectoId.value}/export/${exportacionId}`
  }

  // ==========================================================================
  // Acciones - Progreso
  // ==========================================================================

  /**
   * Carga el progreso de generación por capítulo.
   */
  async function cargarProgreso(): Promise<ProgresoGeneracion[]> {
    if (!proyectoId.value) return []

    try {
      progreso.value = await get<ProgresoGeneracion[]>(
        `/generacion/${proyectoId.value}/progreso`
      )
      return progreso.value
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error cargando progreso'
      throw e
    }
  }

  // ==========================================================================
  // Helpers
  // ==========================================================================

  /**
   * Obtiene el contenido de un capítulo específico.
   */
  function getContenidoCapitulo(numero: number): ContenidoCapitulo | null {
    return contenidoCapitulos.value[numero.toString()] ?? null
  }

  /**
   * Obtiene el progreso de un capítulo específico.
   */
  function getProgresoCapitulo(numero: number): ProgresoGeneracion | null {
    return progreso.value.find(p => p.capitulo_numero === numero) ?? null
  }

  /**
   * Obtiene las observaciones de un capítulo específico.
   */
  function getObservacionesCapitulo(numero: number): ObservacionValidacion[] {
    return observaciones.value.filter(o => o.capitulo_numero === numero)
  }

  /**
   * Selecciona un capítulo para editar.
   */
  function seleccionarCapitulo(numero: number | null): void {
    capituloEditando.value = numero
    contenidoSinGuardar.value = false
  }

  /**
   * Marca que hay contenido sin guardar.
   */
  function marcarSinGuardar(): void {
    contenidoSinGuardar.value = true
  }

  // ==========================================================================
  // Limpiar
  // ==========================================================================

  function limpiar(): void {
    proyectoId.value = null
    documento.value = null
    versiones.value = []
    exportaciones.value = []
    observaciones.value = []
    progreso.value = []
    estadisticas.value = null
    capituloEditando.value = null
    contenidoSinGuardar.value = false
    error.value = null
  }

  // ==========================================================================
  // Return
  // ==========================================================================

  return {
    // Estado
    proyectoId,
    documento,
    versiones,
    exportaciones,
    observaciones,
    progreso,
    estadisticas,

    // Estados de carga
    cargando,
    compilando,
    generandoCapitulo,
    validando,
    exportando,
    guardando,
    error,

    // Editor
    capituloEditando,
    contenidoSinGuardar,

    // Computed
    tieneDocumento,
    contenidoCapitulos,
    capituloActual,
    capitulosGenerados,
    totalPalabras,
    porcentajeCompletitud,
    observacionesPendientes,
    observacionesError,
    observacionesWarning,
    esValido,
    ultimaVersion,
    ultimaExportacion,

    // Acciones - Cargar
    cargarDocumentoCompleto,
    cargarDocumento,
    recargarDocumento,

    // Acciones - Compilar/Generar
    compilarDocumento,
    generarCapitulo,
    regenerarSeccion,

    // Acciones - Actualizar
    actualizarCapitulo,
    actualizarDocumento,

    // Acciones - Versionado
    cargarVersiones,
    crearVersion,
    restaurarVersion,

    // Acciones - Validación
    validarDocumento,
    cargarValidaciones,

    // Acciones - Exportación
    exportarDocumento,
    cargarExportaciones,
    getUrlDescarga,

    // Acciones - Progreso
    cargarProgreso,

    // Helpers
    getContenidoCapitulo,
    getProgresoCapitulo,
    getObservacionesCapitulo,
    seleccionarCapitulo,
    marcarSinGuardar,

    // Limpiar
    limpiar,
  }
})
