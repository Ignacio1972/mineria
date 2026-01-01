/**
 * Store Pinia para Proyectos.
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { proyectosService } from '@/services/proyectos'
import type {
  Proyecto,
  ProyectoConGeometria,
  ProyectoCreate,
  ProyectoUpdate,
  ProyectoGeometriaUpdate,
  FiltrosProyecto,
  EstadoProyecto,
} from '@/types'

export const useProyectosStore = defineStore('proyectos', () => {
  // Estado
  const proyectos = ref<Proyecto[]>([])
  const proyectoActual = ref<ProyectoConGeometria | null>(null)
  const cargando = ref(false)
  const guardando = ref(false)
  const error = ref<string | null>(null)
  const filtros = ref<FiltrosProyecto>({
    page: 1,
    page_size: 20,
  })
  const paginacion = ref({
    total: 0,
    page: 1,
    page_size: 20,
    pages: 0,
  })

  // Computed
  const tieneProyectos = computed(() => proyectos.value.length > 0)

  const proyectosPorEstado = computed(() => {
    const grupos: Record<EstadoProyecto, Proyecto[]> = {
      borrador: [],
      completo: [],
      con_geometria: [],
      analizado: [],
      en_revision: [],
      aprobado: [],
      rechazado: [],
      archivado: [],
    }

    proyectos.value.forEach((p) => {
      grupos[p.estado].push(p)
    })

    return grupos
  })

  const puedeAnalizar = computed(() =>
    proyectoActual.value?.puede_analizar ?? false
  )

  const tieneGeometria = computed(() =>
    proyectoActual.value?.tiene_geometria ?? false
  )

  // Acciones
  async function cargarProyectos(nuevosFiltros?: Partial<FiltrosProyecto>) {
    if (nuevosFiltros) {
      filtros.value = { ...filtros.value, ...nuevosFiltros }
    }

    cargando.value = true
    error.value = null

    try {
      const response = await proyectosService.listar(filtros.value)
      proyectos.value = response.items
      paginacion.value = {
        total: response.total,
        page: response.page,
        page_size: response.page_size,
        pages: response.pages,
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error al cargar proyectos'
      throw e
    } finally {
      cargando.value = false
    }
  }

  async function cargarProyecto(id: string) {
    cargando.value = true
    error.value = null

    try {
      proyectoActual.value = await proyectosService.obtener(id)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error al cargar proyecto'
      throw e
    } finally {
      cargando.value = false
    }
  }

  async function crearProyecto(data: ProyectoCreate): Promise<Proyecto> {
    guardando.value = true
    error.value = null

    try {
      const proyecto = await proyectosService.crear(data)
      proyectos.value.unshift(proyecto)
      return proyecto
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error al crear proyecto'
      throw e
    } finally {
      guardando.value = false
    }
  }

  async function actualizarProyecto(id: string, data: ProyectoUpdate): Promise<Proyecto> {
    guardando.value = true
    error.value = null

    try {
      const proyecto = await proyectosService.actualizar(id, data)

      // Actualizar en lista
      const idx = proyectos.value.findIndex((p) => p.id === id)
      if (idx >= 0) {
        proyectos.value = [
          ...proyectos.value.slice(0, idx),
          proyecto,
          ...proyectos.value.slice(idx + 1),
        ]
      }

      // Actualizar actual
      if (proyectoActual.value?.id === id) {
        proyectoActual.value = { ...proyectoActual.value, ...proyecto }
      }

      return proyecto
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error al actualizar proyecto'
      throw e
    } finally {
      guardando.value = false
    }
  }

  async function actualizarGeometria(id: string, data: ProyectoGeometriaUpdate): Promise<Proyecto> {
    guardando.value = true
    error.value = null

    try {
      const proyecto = await proyectosService.actualizarGeometria(id, data)

      // Actualizar actual
      if (proyectoActual.value?.id === id) {
        proyectoActual.value = {
          ...proyectoActual.value,
          ...proyecto,
          geometria: data.geometria,
        }
      }

      return proyecto
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error al actualizar geometria'
      throw e
    } finally {
      guardando.value = false
    }
  }

  async function cambiarEstado(id: string, nuevoEstado: EstadoProyecto, motivo?: string) {
    guardando.value = true
    error.value = null

    try {
      await proyectosService.cambiarEstado(id, nuevoEstado, motivo)

      // Actualizar en lista
      const idx = proyectos.value.findIndex((p) => p.id === id)
      if (idx >= 0) {
        const existente = proyectos.value[idx] as Proyecto
        proyectos.value[idx] = { ...existente, estado: nuevoEstado } as Proyecto
      }

      // Actualizar actual
      if (proyectoActual.value?.id === id) {
        proyectoActual.value = { ...proyectoActual.value, estado: nuevoEstado }
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error al cambiar estado'
      throw e
    } finally {
      guardando.value = false
    }
  }

  async function archivarProyecto(id: string) {
    guardando.value = true
    error.value = null

    try {
      await proyectosService.archivar(id)

      // Quitar de lista
      proyectos.value = proyectos.value.filter((p) => p.id !== id)

      // Limpiar actual
      if (proyectoActual.value?.id === id) {
        proyectoActual.value = null
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error al archivar proyecto'
      throw e
    } finally {
      guardando.value = false
    }
  }

  function limpiarActual() {
    proyectoActual.value = null
  }

  function limpiarFiltros() {
    filtros.value = { page: 1, page_size: 20 }
  }

  return {
    // Estado
    proyectos,
    proyectoActual,
    cargando,
    guardando,
    error,
    filtros,
    paginacion,
    // Computed
    tieneProyectos,
    proyectosPorEstado,
    puedeAnalizar,
    tieneGeometria,
    // Acciones
    cargarProyectos,
    cargarProyecto,
    crearProyecto,
    actualizarProyecto,
    actualizarGeometria,
    cambiarEstado,
    archivarProyecto,
    limpiarActual,
    limpiarFiltros,
  }
})
