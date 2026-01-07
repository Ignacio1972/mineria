/**
 * Store Pinia para Componentes EIA Checklist y Progreso del Workflow.
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  ComponenteChecklist,
  ComponenteChecklistUpdate,
  ProgresoProyecto,
  FaseProyecto,
  EstadoComponente,
} from '@/types'

const API_BASE = '/api/v1/proyectos'

export const useComponentesStore = defineStore('componentes', () => {
  // Estado
  const componentes = ref<ComponenteChecklist[]>([])
  const progreso = ref<ProgresoProyecto | null>(null)
  const cargando = ref(false)
  const actualizando = ref(false)
  const error = ref<string | null>(null)
  const proyectoIdActual = ref<number | null>(null)

  // Computed
  const componentesPorCapitulo = computed(() => {
    const grupos: Record<number, ComponenteChecklist[]> = {}
    componentes.value.forEach((comp) => {
      const capituloArr = grupos[comp.capitulo]
      if (capituloArr === undefined) {
        grupos[comp.capitulo] = [comp]
      } else {
        capituloArr.push(comp)
      }
    })
    return grupos
  })

  const componentesPorEstado = computed(() => {
    const grupos: Record<EstadoComponente, ComponenteChecklist[]> = {
      pendiente: [],
      en_progreso: [],
      completado: [],
    }
    componentes.value.forEach((comp) => {
      grupos[comp.estado].push(comp)
    })
    return grupos
  })

  const totalComponentes = computed(() => componentes.value.length)

  const componentesCompletados = computed(
    () => componentes.value.filter((c) => c.estado === 'completado').length
  )

  const componentesEnProgreso = computed(
    () => componentes.value.filter((c) => c.estado === 'en_progreso').length
  )

  const componentesPendientes = computed(
    () => componentes.value.filter((c) => c.estado === 'pendiente').length
  )

  const progresoRecopilacion = computed(() => {
    if (componentes.value.length === 0) return 0
    const suma = componentes.value.reduce((acc, c) => acc + c.progreso_porcentaje, 0)
    return Math.round(suma / componentes.value.length)
  })

  const faseActual = computed<FaseProyecto>(() => progreso.value?.fase_actual || 'identificacion')

  const progresoGlobal = computed(() => progreso.value?.progreso_global || 0)

  const tieneChecklist = computed(() => componentes.value.length > 0)

  // Acciones
  async function cargarComponentes(proyectoId: number) {
    cargando.value = true
    error.value = null
    proyectoIdActual.value = proyectoId

    try {
      const response = await fetch(`${API_BASE}/${proyectoId}/componentes-checklist`)
      if (!response.ok) {
        if (response.status === 404) {
          componentes.value = []
          return
        }
        throw new Error(`Error ${response.status}: ${response.statusText}`)
      }
      componentes.value = await response.json()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error al cargar componentes'
      throw e
    } finally {
      cargando.value = false
    }
  }

  async function cargarProgreso(proyectoId: number) {
    cargando.value = true
    error.value = null

    try {
      const response = await fetch(`${API_BASE}/${proyectoId}/progreso`)
      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`)
      }
      progreso.value = await response.json()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error al cargar progreso'
      throw e
    } finally {
      cargando.value = false
    }
  }

  async function cargarTodo(proyectoId: number) {
    await Promise.all([cargarComponentes(proyectoId), cargarProgreso(proyectoId)])
  }

  async function actualizarComponente(
    proyectoId: number,
    componenteId: number,
    data: ComponenteChecklistUpdate
  ): Promise<ComponenteChecklist> {
    actualizando.value = true
    error.value = null

    try {
      const response = await fetch(`${API_BASE}/${proyectoId}/componentes/${componenteId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      })

      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`)
      }

      const componenteActualizado: ComponenteChecklist = await response.json()

      // Actualizar en lista local
      const idx = componentes.value.findIndex((c) => c.id === componenteId)
      if (idx >= 0) {
        componentes.value = [
          ...componentes.value.slice(0, idx),
          componenteActualizado,
          ...componentes.value.slice(idx + 1),
        ]
      }

      // Recargar progreso ya que pudo cambiar
      await cargarProgreso(proyectoId)

      return componenteActualizado
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error al actualizar componente'
      throw e
    } finally {
      actualizando.value = false
    }
  }

  async function marcarComoEnProgreso(proyectoId: number, componenteId: number) {
    return actualizarComponente(proyectoId, componenteId, { estado: 'en_progreso' })
  }

  async function marcarComoCompletado(proyectoId: number, componenteId: number) {
    return actualizarComponente(proyectoId, componenteId, {
      estado: 'completado',
      progreso_porcentaje: 100,
    })
  }

  async function actualizarProgreso(
    proyectoId: number,
    componenteId: number,
    porcentaje: number
  ) {
    return actualizarComponente(proyectoId, componenteId, {
      progreso_porcentaje: porcentaje,
    })
  }

  function obtenerComponente(componenteId: number): ComponenteChecklist | undefined {
    return componentes.value.find((c) => c.id === componenteId)
  }

  function obtenerComponentePorClave(clave: string): ComponenteChecklist | undefined {
    return componentes.value.find((c) => c.componente === clave)
  }

  function limpiar() {
    componentes.value = []
    progreso.value = null
    proyectoIdActual.value = null
    error.value = null
  }

  return {
    // Estado
    componentes,
    progreso,
    cargando,
    actualizando,
    error,
    proyectoIdActual,
    // Computed
    componentesPorCapitulo,
    componentesPorEstado,
    totalComponentes,
    componentesCompletados,
    componentesEnProgreso,
    componentesPendientes,
    progresoRecopilacion,
    faseActual,
    progresoGlobal,
    tieneChecklist,
    // Acciones
    cargarComponentes,
    cargarProgreso,
    cargarTodo,
    actualizarComponente,
    marcarComoEnProgreso,
    marcarComoCompletado,
    actualizarProgreso,
    obtenerComponente,
    obtenerComponentePorClave,
    limpiar,
  }
})
