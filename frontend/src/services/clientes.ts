/**
 * Servicio API para Clientes.
 */
import { get, post, put, del } from './api'
import type {
  Cliente,
  ClienteCreate,
  ClienteUpdate,
  ClienteListResponse,
  Proyecto,
} from '@/types'

const BASE_URL = '/clientes'

export const clientesService = {
  /**
   * Listar clientes con paginacion y filtros.
   */
  async listar(params?: {
    busqueda?: string
    activo?: boolean
    page?: number
    page_size?: number
  }): Promise<ClienteListResponse> {
    return get(BASE_URL, { params })
  },

  /**
   * Obtener cliente por ID.
   */
  async obtener(id: string): Promise<Cliente> {
    return get(`${BASE_URL}/${id}`)
  },

  /**
   * Crear nuevo cliente.
   */
  async crear(data: ClienteCreate): Promise<Cliente> {
    return post(BASE_URL, data)
  },

  /**
   * Actualizar cliente.
   */
  async actualizar(id: string, data: ClienteUpdate): Promise<Cliente> {
    return put(`${BASE_URL}/${id}`, data)
  },

  /**
   * Eliminar (desactivar) cliente.
   */
  async eliminar(id: string): Promise<void> {
    return del(`${BASE_URL}/${id}`)
  },

  /**
   * Obtener proyectos del cliente.
   */
  async obtenerProyectos(id: string): Promise<Proyecto[]> {
    return get(`${BASE_URL}/${id}/proyectos`)
  },
}
