/**
 * Servicio API para Proyectos.
 */
import { get, post, put, patch, del } from './api'
import type {
  Proyecto,
  ProyectoConGeometria,
  ProyectoCreate,
  ProyectoUpdate,
  ProyectoGeometriaUpdate,
  ProyectoListResponse,
  FiltrosProyecto,
  EstadoProyecto,
  AnalisisResumen,
} from '@/types'

const BASE_URL = '/proyectos'

export const proyectosService = {
  /**
   * Listar proyectos con paginacion y filtros.
   */
  async listar(filtros?: FiltrosProyecto): Promise<ProyectoListResponse> {
    return get(BASE_URL, { params: filtros })
  },

  /**
   * Obtener proyecto por ID (con geometria).
   */
  async obtener(id: string): Promise<ProyectoConGeometria> {
    return get(`${BASE_URL}/${id}`)
  },

  /**
   * Crear nuevo proyecto.
   */
  async crear(data: ProyectoCreate): Promise<Proyecto> {
    return post(BASE_URL, data)
  },

  /**
   * Actualizar proyecto (sin geometria).
   */
  async actualizar(id: string, data: ProyectoUpdate): Promise<Proyecto> {
    return put(`${BASE_URL}/${id}`, data)
  },

  /**
   * Actualizar solo geometria.
   */
  async actualizarGeometria(id: string, data: ProyectoGeometriaUpdate): Promise<Proyecto> {
    return patch(`${BASE_URL}/${id}/geometria`, data)
  },

  /**
   * Cambiar estado del proyecto.
   */
  async cambiarEstado(id: string, nuevoEstado: EstadoProyecto, motivo?: string): Promise<void> {
    return patch(`${BASE_URL}/${id}/estado`, {
      nuevo_estado: nuevoEstado,
      motivo,
    })
  },

  /**
   * Archivar proyecto.
   */
  async archivar(id: string): Promise<void> {
    return del(`${BASE_URL}/${id}`)
  },

  /**
   * Obtener historial de analisis.
   */
  async obtenerAnalisis(id: string): Promise<AnalisisResumen[]> {
    return get(`${BASE_URL}/${id}/analisis`)
  },
}
