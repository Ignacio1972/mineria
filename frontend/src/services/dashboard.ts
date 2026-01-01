/**
 * Servicio API para Dashboard.
 */
import { get, del } from './api'

export interface DashboardStats {
  total_clientes: number
  total_proyectos: number
  proyectos_borrador: number
  proyectos_analizados: number
  analisis_semana: number
  total_eia: number
  total_dia: number
}

export interface AnalisisReciente {
  id: string
  proyecto_id: string
  proyecto_nombre: string
  via_ingreso: 'EIA' | 'DIA'
  confianza: number
  fecha: string
  alertas_criticas: number
}

export interface EliminarAnalisisResponse {
  mensaje: string
  analisis_id: number
  proyecto_id: number
  era_ultimo_analisis: boolean
  nuevo_estado_proyecto: string | null
}

export const dashboardService = {
  /**
   * Obtener estadisticas del dashboard.
   */
  async obtenerEstadisticas(): Promise<DashboardStats> {
    return get('/dashboard/stats')
  },

  /**
   * Obtener analisis recientes.
   */
  async obtenerAnalisisRecientes(limite = 5): Promise<AnalisisReciente[]> {
    return get('/dashboard/analisis-recientes', { params: { limite } })
  },

  /**
   * Eliminar un análisis.
   */
  async eliminarAnalisis(analisisId: number): Promise<EliminarAnalisisResponse> {
    return del(`/prefactibilidad/analisis/${analisisId}`)
  },
}
