/**
 * Store Pinia para gestión del corpus RAG.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  listarCategorias,
  listarTemas,
  listarColecciones,
  listarDocumentos,
  obtenerDocumento,
  crearDocumento,
  actualizarDocumento,
  eliminarDocumento,
  obtenerFragmentos,
  reprocesarDocumento,
  descargarArchivo,
  descargarContenido,
} from '@/services/corpus'
import type {
  Categoria,
  CategoriaConHijos,
  Tema,
  GrupoTema,
  Coleccion,
  DocumentoResumen,
  DocumentoDetalle,
  DocumentoCreateData,
  DocumentoUpdateData,
  DocumentoFiltros,
  Fragmento,
} from '@/types'

export const useCorpusStore = defineStore('corpus', () => {
  // ============================================================================
  // STATE
  // ============================================================================

  // Categorias
  const categorias = ref<Categoria[]>([])
  const cargandoCategorias = ref(false)

  // Temas
  const temas = ref<Tema[]>([])
  const cargandoTemas = ref(false)

  // Colecciones
  const colecciones = ref<Coleccion[]>([])
  const cargandoColecciones = ref(false)

  // Documentos
  const documentos = ref<DocumentoResumen[]>([])
  const documentoActual = ref<DocumentoDetalle | null>(null)
  const totalDocumentos = ref(0)
  const cargandoDocumentos = ref(false)
  const cargandoDocumento = ref(false)

  // Fragmentos del documento actual
  const fragmentos = ref<Fragmento[]>([])
  const totalFragmentos = ref(0)
  const cargandoFragmentos = ref(false)

  // Filtros activos
  const filtrosActivos = ref<DocumentoFiltros>({
    limite: 100,
    offset: 0,
    orden: 'fecha_desc',
  })

  // UI State
  const error = ref<string | null>(null)
  const procesando = ref(false)

  // ============================================================================
  // COMPUTED
  // ============================================================================

  /**
   * Categorias organizadas como arbol jerarquico.
   */
  const categoriasArbol = computed<CategoriaConHijos[]>(() => {
    const mapa = new Map<number, CategoriaConHijos>()

    // Inicializar todas las categorias con hijos vacio
    categorias.value.forEach((cat) => {
      mapa.set(cat.id, { ...cat, hijos: [] })
    })

    const raices: CategoriaConHijos[] = []

    // Construir arbol
    categorias.value.forEach((cat) => {
      const nodo = mapa.get(cat.id)!
      if (cat.parent_id === null) {
        raices.push(nodo)
      } else {
        const padre = mapa.get(cat.parent_id)
        if (padre) {
          padre.hijos.push(nodo)
        } else {
          raices.push(nodo)
        }
      }
    })

    // Ordenar por orden
    const ordenar = (lista: CategoriaConHijos[]) => {
      lista.sort((a, b) => a.orden - b.orden)
      lista.forEach((item) => ordenar(item.hijos))
    }
    ordenar(raices)

    return raices
  })

  /**
   * Temas agrupados por grupo.
   */
  const temasAgrupados = computed<Record<GrupoTema, Tema[]>>(() => {
    const grupos: Record<GrupoTema, Tema[]> = {
      componente_ambiental: [],
      trigger_art11: [],
      etapa_seia: [],
      sector: [],
      otro: [],
    }

    temas.value.forEach((tema) => {
      if (grupos[tema.grupo]) {
        grupos[tema.grupo].push(tema)
      } else {
        grupos.otro.push(tema)
      }
    })

    return grupos
  })

  /**
   * Total de paginas para paginacion.
   */
  const totalPaginas = computed(() =>
    Math.ceil(totalDocumentos.value / (filtrosActivos.value.limite || 100))
  )

  /**
   * Pagina actual (1-indexed).
   */
  const paginaActual = computed(() => {
    const offset = filtrosActivos.value.offset || 0
    const limite = filtrosActivos.value.limite || 100
    return Math.floor(offset / limite) + 1
  })

  /**
   * Indica si hay documento seleccionado.
   */
  const tieneDocumentoSeleccionado = computed(() => documentoActual.value !== null)

  // ============================================================================
  // ACTIONS - CATEGORIAS
  // ============================================================================

  async function cargarCategorias() {
    if (cargandoCategorias.value) return
    cargandoCategorias.value = true
    error.value = null

    try {
      categorias.value = await listarCategorias()
    } catch (e) {
      error.value = (e as { detail?: string })?.detail || 'Error cargando categorias'
      console.error('Error cargando categorias:', e)
    } finally {
      cargandoCategorias.value = false
    }
  }

  // ============================================================================
  // ACTIONS - TEMAS
  // ============================================================================

  async function cargarTemas(grupo?: string) {
    if (cargandoTemas.value) return
    cargandoTemas.value = true
    error.value = null

    try {
      temas.value = await listarTemas(grupo)
    } catch (e) {
      error.value = (e as { detail?: string })?.detail || 'Error cargando temas'
      console.error('Error cargando temas:', e)
    } finally {
      cargandoTemas.value = false
    }
  }

  // ============================================================================
  // ACTIONS - COLECCIONES
  // ============================================================================

  async function cargarColecciones() {
    if (cargandoColecciones.value) return
    cargandoColecciones.value = true
    error.value = null

    try {
      colecciones.value = await listarColecciones()
    } catch (e) {
      error.value = (e as { detail?: string })?.detail || 'Error cargando colecciones'
      console.error('Error cargando colecciones:', e)
    } finally {
      cargandoColecciones.value = false
    }
  }

  // ============================================================================
  // ACTIONS - DOCUMENTOS
  // ============================================================================

  async function cargarDocumentos(filtros?: DocumentoFiltros) {
    cargandoDocumentos.value = true
    error.value = null

    // Actualizar filtros si se proporcionan
    if (filtros) {
      filtrosActivos.value = { ...filtrosActivos.value, ...filtros }
    }

    try {
      const response = await listarDocumentos(filtrosActivos.value)
      documentos.value = response.documentos
      totalDocumentos.value = response.total
    } catch (e) {
      error.value = (e as { detail?: string })?.detail || 'Error cargando documentos'
      console.error('Error cargando documentos:', e)
    } finally {
      cargandoDocumentos.value = false
    }
  }

  async function seleccionarDocumento(id: number) {
    cargandoDocumento.value = true
    error.value = null

    try {
      documentoActual.value = await obtenerDocumento(id)
      // Cargar fragmentos automaticamente
      await cargarFragmentosDocumento()
    } catch (e) {
      error.value = (e as { detail?: string })?.detail || 'Error cargando documento'
      console.error('Error cargando documento:', e)
      documentoActual.value = null
    } finally {
      cargandoDocumento.value = false
    }
  }

  async function crearNuevoDocumento(
    data: DocumentoCreateData,
    archivo?: File,
    procesarAuto = true
  ): Promise<DocumentoResumen | null> {
    procesando.value = true
    error.value = null

    try {
      const nuevoDoc = await crearDocumento(data, archivo, procesarAuto)
      // Recargar lista
      await cargarDocumentos()
      return nuevoDoc
    } catch (e) {
      error.value = (e as { detail?: string })?.detail || 'Error creando documento'
      console.error('Error creando documento:', e)
      return null
    } finally {
      procesando.value = false
    }
  }

  async function actualizarDocumentoActual(data: DocumentoUpdateData): Promise<boolean> {
    if (!documentoActual.value) return false

    procesando.value = true
    error.value = null

    try {
      await actualizarDocumento(documentoActual.value.id, data)
      // Recargar documento y lista
      await seleccionarDocumento(documentoActual.value.id)
      await cargarDocumentos()
      return true
    } catch (e) {
      error.value = (e as { detail?: string })?.detail || 'Error actualizando documento'
      console.error('Error actualizando documento:', e)
      return false
    } finally {
      procesando.value = false
    }
  }

  async function eliminarDocumentoActual(): Promise<boolean> {
    if (!documentoActual.value) return false

    procesando.value = true
    error.value = null

    try {
      await eliminarDocumento(documentoActual.value.id)
      documentoActual.value = null
      fragmentos.value = []
      // Recargar lista
      await cargarDocumentos()
      return true
    } catch (e) {
      error.value = (e as { detail?: string })?.detail || 'Error eliminando documento'
      console.error('Error eliminando documento:', e)
      return false
    } finally {
      procesando.value = false
    }
  }

  // ============================================================================
  // ACTIONS - FRAGMENTOS
  // ============================================================================

  async function cargarFragmentosDocumento(limite = 100, offset = 0) {
    if (!documentoActual.value) return

    cargandoFragmentos.value = true

    try {
      const response = await obtenerFragmentos(documentoActual.value.id, limite, offset)
      fragmentos.value = response.fragmentos
      totalFragmentos.value = response.total
    } catch (e) {
      console.error('Error cargando fragmentos:', e)
      fragmentos.value = []
      totalFragmentos.value = 0
    } finally {
      cargandoFragmentos.value = false
    }
  }

  async function reprocesarDocumentoActual(): Promise<boolean> {
    if (!documentoActual.value) return false

    procesando.value = true
    error.value = null

    try {
      await reprocesarDocumento(documentoActual.value.id)
      // Recargar documento y fragmentos
      await seleccionarDocumento(documentoActual.value.id)
      return true
    } catch (e) {
      error.value = (e as { detail?: string })?.detail || 'Error reprocesando documento'
      console.error('Error reprocesando documento:', e)
      return false
    } finally {
      procesando.value = false
    }
  }

  // ============================================================================
  // ACTIONS - ARCHIVOS
  // ============================================================================

  async function descargarArchivoDocumento() {
    if (!documentoActual.value?.archivo_nombre) return

    try {
      await descargarArchivo(documentoActual.value.id, documentoActual.value.archivo_nombre)
    } catch (e) {
      error.value = (e as { detail?: string })?.detail || 'Error descargando archivo'
      console.error('Error descargando archivo:', e)
    }
  }

  async function descargarContenidoDocumento() {
    if (!documentoActual.value) return

    try {
      const nombre = `${documentoActual.value.tipo}_${documentoActual.value.titulo.substring(0, 50)}.txt`
      await descargarContenido(documentoActual.value.id, nombre)
    } catch (e) {
      error.value = (e as { detail?: string })?.detail || 'Error descargando contenido'
      console.error('Error descargando contenido:', e)
    }
  }

  // ============================================================================
  // ACTIONS - FILTROS Y PAGINACION
  // ============================================================================

  function aplicarFiltro(filtro: Partial<DocumentoFiltros>) {
    // Resetear offset al cambiar filtros (excepto paginacion)
    const resetOffset = !('offset' in filtro)
    filtrosActivos.value = {
      ...filtrosActivos.value,
      ...filtro,
      ...(resetOffset ? { offset: 0 } : {}),
    }
    cargarDocumentos()
  }

  function limpiarFiltros() {
    filtrosActivos.value = {
      limite: 100,
      offset: 0,
      orden: 'fecha_desc',
    }
    cargarDocumentos()
  }

  function irAPagina(pagina: number) {
    const limite = filtrosActivos.value.limite || 100
    const offset = (pagina - 1) * limite
    aplicarFiltro({ offset })
  }

  // ============================================================================
  // ACTIONS - INICIALIZACION
  // ============================================================================

  async function inicializar() {
    await Promise.all([cargarCategorias(), cargarTemas(), cargarColecciones(), cargarDocumentos()])
  }

  function limpiarDocumentoActual() {
    documentoActual.value = null
    fragmentos.value = []
    totalFragmentos.value = 0
  }

  function limpiarError() {
    error.value = null
  }

  // ============================================================================
  // RETURN
  // ============================================================================

  return {
    // State
    categorias,
    cargandoCategorias,
    temas,
    cargandoTemas,
    colecciones,
    cargandoColecciones,
    documentos,
    documentoActual,
    totalDocumentos,
    cargandoDocumentos,
    cargandoDocumento,
    fragmentos,
    totalFragmentos,
    cargandoFragmentos,
    filtrosActivos,
    error,
    procesando,

    // Computed
    categoriasArbol,
    temasAgrupados,
    totalPaginas,
    paginaActual,
    tieneDocumentoSeleccionado,

    // Actions - Categorias
    cargarCategorias,

    // Actions - Temas
    cargarTemas,

    // Actions - Colecciones
    cargarColecciones,

    // Actions - Documentos
    cargarDocumentos,
    seleccionarDocumento,
    crearNuevoDocumento,
    actualizarDocumentoActual,
    eliminarDocumentoActual,

    // Actions - Fragmentos
    cargarFragmentosDocumento,
    reprocesarDocumentoActual,

    // Actions - Archivos
    descargarArchivoDocumento,
    descargarContenidoDocumento,

    // Actions - Filtros
    aplicarFiltro,
    limpiarFiltros,
    irAPagina,

    // Actions - Inicializacion
    inicializar,
    limpiarDocumentoActual,
    limpiarError,
  }
})
