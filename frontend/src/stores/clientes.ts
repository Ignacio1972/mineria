/**
 * Store Pinia para Clientes.
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { clientesService } from '@/services/clientes'
import type { Cliente, ClienteCreate, ClienteUpdate } from '@/types'

export const useClientesStore = defineStore('clientes', () => {
  // Estado
  const clientes = ref<Cliente[]>([])
  const clienteActual = ref<Cliente | null>(null)
  const cargando = ref(false)
  const error = ref<string | null>(null)
  const paginacion = ref({
    total: 0,
    page: 1,
    page_size: 20,
    pages: 0,
  })

  // Computed
  const clientesActivos = computed(() =>
    clientes.value.filter((c) => c.activo)
  )

  const tieneClientes = computed(() => clientes.value.length > 0)

  // Acciones
  async function cargarClientes(params?: {
    busqueda?: string
    page?: number
    page_size?: number
  }) {
    cargando.value = true
    error.value = null

    try {
      const response = await clientesService.listar({
        activo: true,
        ...params,
      })
      clientes.value = response.items
      paginacion.value = {
        total: response.total,
        page: response.page,
        page_size: response.page_size,
        pages: response.pages,
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error al cargar clientes'
      throw e
    } finally {
      cargando.value = false
    }
  }

  async function cargarCliente(id: string) {
    cargando.value = true
    error.value = null

    try {
      clienteActual.value = await clientesService.obtener(id)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error al cargar cliente'
      throw e
    } finally {
      cargando.value = false
    }
  }

  async function crearCliente(data: ClienteCreate): Promise<Cliente> {
    cargando.value = true
    error.value = null

    try {
      const cliente = await clientesService.crear(data)
      clientes.value.unshift(cliente)
      return cliente
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error al crear cliente'
      throw e
    } finally {
      cargando.value = false
    }
  }

  async function actualizarCliente(id: string, data: ClienteUpdate): Promise<Cliente> {
    cargando.value = true
    error.value = null

    try {
      const cliente = await clientesService.actualizar(id, data)

      // Actualizar en lista
      const idx = clientes.value.findIndex((c) => c.id === id)
      if (idx >= 0) {
        clientes.value = [
          ...clientes.value.slice(0, idx),
          cliente,
          ...clientes.value.slice(idx + 1),
        ]
      }

      // Actualizar actual si corresponde
      if (clienteActual.value?.id === id) {
        clienteActual.value = cliente
      }

      return cliente
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error al actualizar cliente'
      throw e
    } finally {
      cargando.value = false
    }
  }

  async function eliminarCliente(id: string) {
    cargando.value = true
    error.value = null

    try {
      await clientesService.eliminar(id)

      // Quitar de lista
      clientes.value = clientes.value.filter((c) => c.id !== id)

      // Limpiar actual si corresponde
      if (clienteActual.value?.id === id) {
        clienteActual.value = null
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error al eliminar cliente'
      throw e
    } finally {
      cargando.value = false
    }
  }

  function limpiarActual() {
    clienteActual.value = null
  }

  return {
    // Estado
    clientes,
    clienteActual,
    cargando,
    error,
    paginacion,
    // Computed
    clientesActivos,
    tieneClientes,
    // Acciones
    cargarClientes,
    cargarCliente,
    crearCliente,
    actualizarCliente,
    eliminarCliente,
    limpiarActual,
  }
})
