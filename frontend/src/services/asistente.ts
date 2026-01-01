/**
 * Servicio API para el Asistente IA.
 */
import api from './api'
import type {
  ChatRequest,
  ChatResponse,
  ConfirmacionAccion,
  ResultadoAccion,
  Conversacion,
  ConversacionConMensajes,
  AccionPendiente,
  NotificacionProactiva,
  FeedbackCreate,
  Feedback,
  HerramientasDisponibles,
  BusquedaWebRequest,
  BusquedaWebResponse,
  RouterInfo,
} from '@/types'

const BASE_URL = '/asistente'

export const asistenteService = {
  /**
   * Envia un mensaje al asistente.
   */
  async chat(request: ChatRequest): Promise<ChatResponse> {
    const { data } = await api.post<ChatResponse>(`${BASE_URL}/chat`, request)
    return data
  },

  /**
   * Confirma o cancela una accion pendiente.
   */
  async confirmarAccion(confirmacion: ConfirmacionAccion): Promise<ResultadoAccion> {
    const { data } = await api.post<ResultadoAccion>(`${BASE_URL}/confirm`, confirmacion)
    return data
  },

  /**
   * Lista las conversaciones de una sesion.
   */
  async listarConversaciones(sessionId: string, limite = 20): Promise<Conversacion[]> {
    const { data } = await api.get<Conversacion[]>(`${BASE_URL}/conversaciones`, {
      params: { session_id: sessionId, limite }
    })
    return data
  },

  /**
   * Obtiene una conversacion con sus mensajes.
   */
  async obtenerConversacion(conversacionId: string): Promise<ConversacionConMensajes> {
    const { data } = await api.get<ConversacionConMensajes>(
      `${BASE_URL}/conversaciones/${conversacionId}`
    )
    return data
  },

  /**
   * Elimina una conversacion.
   */
  async eliminarConversacion(conversacionId: string): Promise<void> {
    await api.delete(`${BASE_URL}/conversaciones/${conversacionId}`)
  },

  /**
   * Lista las acciones pendientes.
   */
  async listarAccionesPendientes(sessionId: string): Promise<AccionPendiente[]> {
    const { data } = await api.get<AccionPendiente[]>(`${BASE_URL}/acciones-pendientes`, {
      params: { session_id: sessionId }
    })
    return data
  },

  /**
   * Lista las herramientas disponibles.
   */
  async listarHerramientas(): Promise<HerramientasDisponibles> {
    const { data } = await api.get<HerramientasDisponibles>(`${BASE_URL}/herramientas`)
    return data
  },

  /**
   * Obtiene estadisticas de herramientas.
   */
  async estadisticasHerramientas(): Promise<Record<string, number>> {
    const { data } = await api.get<Record<string, number>>(`${BASE_URL}/herramientas/stats`)
    return data
  },

  /**
   * Crea feedback sobre un mensaje.
   */
  async crearFeedback(feedback: FeedbackCreate): Promise<Feedback> {
    const { data } = await api.post<Feedback>(`${BASE_URL}/feedback`, feedback)
    return data
  },

  /**
   * Lista notificaciones proactivas.
   */
  async listarNotificaciones(
    sessionId: string,
    soloNoLeidas = true,
    limite = 10
  ): Promise<NotificacionProactiva[]> {
    const { data } = await api.get<NotificacionProactiva[]>(`${BASE_URL}/notificaciones`, {
      params: {
        session_id: sessionId,
        solo_no_leidas: soloNoLeidas,
        limite,
      }
    })
    return data
  },

  /**
   * Marca una notificacion como leida.
   */
  async marcarNotificacionLeida(
    notificacionId: string,
    accionTomada?: string
  ): Promise<void> {
    await api.post(`${BASE_URL}/notificaciones/${notificacionId}/leer`, null, {
      params: { accion_tomada: accionTomada }
    })
  },

  /**
   * Verifica el estado del servicio.
   */
  async healthCheck(): Promise<{ status: string; herramientas_registradas: number }> {
    const { data } = await api.get(`${BASE_URL}/health`)
    return data
  },

  // ===== Búsqueda Web (Perplexity) =====

  /**
   * Realiza búsqueda web actualizada usando Perplexity.
   */
  async buscarWeb(request: BusquedaWebRequest): Promise<BusquedaWebResponse> {
    const { data } = await api.post<BusquedaWebResponse>('/llm/buscar-web', request)
    return data
  },

  /**
   * Obtiene información del router LLM.
   */
  async obtenerRouterInfo(): Promise<RouterInfo> {
    const { data } = await api.get<RouterInfo>('/llm/router/info')
    return data
  },

  /**
   * Health check del router LLM.
   */
  async healthCheckRouter(): Promise<Record<string, unknown>> {
    const { data } = await api.get('/llm/router/health')
    return data
  },
}

export default asistenteService
