/**
 * Store Pinia para el Asistente IA.
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { v4 as uuidv4 } from 'uuid'
import { asistenteService } from '@/services/asistente'
import type {
  MensajeResponse,
  Conversacion,
  ConversacionConMensajes,
  AccionPendiente,
  NotificacionProactiva,
  ChatRequest,
  ChatResponse,
  ConfirmacionAccion,
  HerramientaInfo,
  EstadoAsistente,
} from '@/types'

// Constante para session_id (en produccion vendria de auth)
const getSessionId = (): string => {
  const stored = localStorage.getItem('asistente_session_id')
  if (stored) {
    return stored
  }
  const newId = uuidv4()
  localStorage.setItem('asistente_session_id', newId)
  return newId
}

export const useAsistenteStore = defineStore('asistente', () => {
  // ==========================================================================
  // Estado
  // ==========================================================================

  // Session
  const sessionId = ref<string>(getSessionId())

  // Conversacion actual
  const conversacionActual = ref<ConversacionConMensajes | null>(null)
  const conversaciones = ref<Conversacion[]>([])

  // Mensajes de la conversacion activa
  const mensajes = ref<MensajeResponse[]>([])

  // Estado de la UI
  const estado = ref<EstadoAsistente>({
    conectado: true,
    escribiendo: false,
    procesando: false,
  })

  // Acciones pendientes
  const accionesPendientes = ref<AccionPendiente[]>([])
  const accionActual = ref<AccionPendiente | null>(null)

  // Notificaciones
  const notificaciones = ref<NotificacionProactiva[]>([])
  const notificacionesNoLeidas = ref<number>(0)

  // Herramientas
  const herramientas = ref<HerramientaInfo[]>([])

  // Control de carga
  const cargando = ref(false)
  const enviando = ref(false)
  const error = ref<string | null>(null)

  // Contexto del proyecto activo
  const proyectoContextoId = ref<number | null>(null)
  const vistaActual = ref<string>('dashboard')

  // ==========================================================================
  // Computed
  // ==========================================================================

  const tieneConversacionActiva = computed(() => conversacionActual.value !== null)

  const totalMensajes = computed(() => mensajes.value.length)

  const ultimoMensaje = computed(() =>
    mensajes.value.length > 0 ? mensajes.value[mensajes.value.length - 1] : null
  )

  const mensajesUsuario = computed(() =>
    mensajes.value.filter((m) => m.rol === 'user')
  )

  const mensajesAsistente = computed(() =>
    mensajes.value.filter((m) => m.rol === 'assistant')
  )

  const tieneAccionesPendientes = computed(() => accionesPendientes.value.length > 0)

  const tieneNotificaciones = computed(() => notificacionesNoLeidas.value > 0)

  // ==========================================================================
  // Acciones - Chat
  // ==========================================================================

  /**
   * Envia un mensaje al asistente.
   */
  async function enviarMensaje(contenido: string): Promise<ChatResponse | null> {
    if (!contenido.trim()) return null

    enviando.value = true
    estado.value.procesando = true
    error.value = null

    try {
      const request: ChatRequest = {
        mensaje: contenido.trim(),
        session_id: sessionId.value,
        conversacion_id: conversacionActual.value?.id,
        proyecto_contexto_id: proyectoContextoId.value ?? undefined,
        vista_actual: vistaActual.value,
      }

      // Agregar mensaje del usuario localmente
      const mensajeUsuario: MensajeResponse = {
        id: uuidv4(),
        conversacion_id: conversacionActual.value?.id || '',
        rol: 'user',
        contenido: contenido.trim(),
        created_at: new Date().toISOString(),
      }
      mensajes.value.push(mensajeUsuario)

      // Indicar que el asistente esta escribiendo
      estado.value.escribiendo = true

      // Enviar al backend
      const respuesta = await asistenteService.chat(request)

      // Actualizar conversacion si es nueva
      if (!conversacionActual.value) {
        conversacionActual.value = {
          id: respuesta.conversacion_id,
          session_id: sessionId.value,
          titulo: contenido.substring(0, 50),
          vista_actual: vistaActual.value,
          activa: true,
          total_mensajes: 2,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          mensajes: [],
        }
      }

      // Agregar respuesta del asistente
      mensajes.value.push(respuesta.mensaje)

      // Manejar accion pendiente si existe
      if (respuesta.accion_pendiente) {
        accionActual.value = respuesta.accion_pendiente
        accionesPendientes.value.push(respuesta.accion_pendiente)
      }

      return respuesta
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error al enviar mensaje'
      throw e
    } finally {
      enviando.value = false
      estado.value.procesando = false
      estado.value.escribiendo = false
    }
  }

  /**
   * Confirma una accion pendiente.
   */
  async function confirmarAccion(accionId: string, confirmada: boolean, comentario?: string): Promise<void> {
    cargando.value = true
    error.value = null

    try {
      const confirmacion: ConfirmacionAccion = {
        accion_id: accionId,
        confirmada,
        comentario,
      }

      const resultado = await asistenteService.confirmarAccion(confirmacion)

      // Actualizar estado de la accion
      const index = accionesPendientes.value.findIndex((a) => a.id === accionId)
      if (index >= 0) {
        accionesPendientes.value.splice(index, 1)
      }

      if (accionActual.value?.id === accionId) {
        accionActual.value = null
      }

      // Agregar mensaje con resultado
      const mensajeResultado: MensajeResponse = {
        id: uuidv4(),
        conversacion_id: conversacionActual.value?.id || '',
        rol: 'assistant',
        contenido: resultado.mensaje,
        created_at: new Date().toISOString(),
      }
      mensajes.value.push(mensajeResultado)

    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error al confirmar accion'
      throw e
    } finally {
      cargando.value = false
    }
  }

  // ==========================================================================
  // Acciones - Conversaciones
  // ==========================================================================

  /**
   * Carga las conversaciones de la sesion.
   */
  async function cargarConversaciones(): Promise<void> {
    cargando.value = true
    error.value = null

    try {
      conversaciones.value = await asistenteService.listarConversaciones(sessionId.value)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error al cargar conversaciones'
      throw e
    } finally {
      cargando.value = false
    }
  }

  /**
   * Carga una conversacion especifica con sus mensajes.
   */
  async function cargarConversacion(conversacionId: string): Promise<void> {
    cargando.value = true
    error.value = null

    try {
      conversacionActual.value = await asistenteService.obtenerConversacion(conversacionId)
      mensajes.value = conversacionActual.value.mensajes
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error al cargar conversacion'
      throw e
    } finally {
      cargando.value = false
    }
  }

  /**
   * Inicia una nueva conversacion.
   */
  function nuevaConversacion(): void {
    conversacionActual.value = null
    mensajes.value = []
    accionActual.value = null
    error.value = null
  }

  /**
   * Elimina una conversacion.
   */
  async function eliminarConversacion(conversacionId: string): Promise<void> {
    try {
      await asistenteService.eliminarConversacion(conversacionId)
      conversaciones.value = conversaciones.value.filter((c) => c.id !== conversacionId)

      if (conversacionActual.value?.id === conversacionId) {
        nuevaConversacion()
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error al eliminar conversacion'
      throw e
    }
  }

  // ==========================================================================
  // Acciones - Notificaciones
  // ==========================================================================

  /**
   * Carga las notificaciones.
   */
  async function cargarNotificaciones(): Promise<void> {
    try {
      notificaciones.value = await asistenteService.listarNotificaciones(sessionId.value)
      notificacionesNoLeidas.value = notificaciones.value.length
    } catch (e) {
      console.error('Error cargando notificaciones:', e)
    }
  }

  /**
   * Marca una notificacion como leida.
   */
  async function marcarNotificacionLeida(notificacionId: string, accionTomada?: string): Promise<void> {
    try {
      await asistenteService.marcarNotificacionLeida(notificacionId, accionTomada)
      notificaciones.value = notificaciones.value.filter((n) => n.id !== notificacionId)
      notificacionesNoLeidas.value = Math.max(0, notificacionesNoLeidas.value - 1)
    } catch (e) {
      console.error('Error marcando notificacion:', e)
    }
  }

  // ==========================================================================
  // Acciones - Herramientas
  // ==========================================================================

  /**
   * Carga las herramientas disponibles.
   */
  async function cargarHerramientas(): Promise<void> {
    try {
      const response = await asistenteService.listarHerramientas()
      herramientas.value = response.herramientas
    } catch (e) {
      console.error('Error cargando herramientas:', e)
    }
  }

  // ==========================================================================
  // Acciones - Contexto
  // ==========================================================================

  /**
   * Establece el proyecto de contexto y lo persiste en localStorage.
   */
  function setProyectoContexto(proyectoId: number | null): void {
    proyectoContextoId.value = proyectoId
    if (proyectoId !== null) {
      localStorage.setItem('ultimo_proyecto_contexto', String(proyectoId))
    }
  }

  /**
   * Recupera el proyecto de contexto desde localStorage.
   */
  function recuperarProyectoContexto(): number | null {
    const stored = localStorage.getItem('ultimo_proyecto_contexto')
    if (stored) {
      const id = parseInt(stored, 10)
      if (!isNaN(id)) {
        proyectoContextoId.value = id
        return id
      }
    }
    return null
  }

  /**
   * Establece la vista actual.
   */
  function setVistaActual(vista: string): void {
    vistaActual.value = vista
  }

  // ==========================================================================
  // Acciones - Feedback
  // ==========================================================================

  /**
   * Envia feedback sobre un mensaje.
   */
  async function enviarFeedback(
    mensajeId: string,
    esUtil: boolean,
    valoracion?: number,
    comentario?: string
  ): Promise<void> {
    try {
      await asistenteService.crearFeedback({
        mensaje_id: mensajeId,
        es_util: esUtil,
        valoracion,
        comentario,
        categorias_problema: [],
      })
    } catch (e) {
      console.error('Error enviando feedback:', e)
    }
  }

  // ==========================================================================
  // Limpiar estado
  // ==========================================================================

  function limpiar(): void {
    conversacionActual.value = null
    mensajes.value = []
    accionActual.value = null
    accionesPendientes.value = []
    error.value = null
  }

  // ==========================================================================
  // Return
  // ==========================================================================

  return {
    // Estado
    sessionId,
    conversacionActual,
    conversaciones,
    mensajes,
    estado,
    accionesPendientes,
    accionActual,
    notificaciones,
    notificacionesNoLeidas,
    herramientas,
    cargando,
    enviando,
    error,
    proyectoContextoId,
    vistaActual,

    // Computed
    tieneConversacionActiva,
    totalMensajes,
    ultimoMensaje,
    mensajesUsuario,
    mensajesAsistente,
    tieneAccionesPendientes,
    tieneNotificaciones,

    // Acciones - Chat
    enviarMensaje,
    confirmarAccion,

    // Acciones - Conversaciones
    cargarConversaciones,
    cargarConversacion,
    nuevaConversacion,
    eliminarConversacion,

    // Acciones - Notificaciones
    cargarNotificaciones,
    marcarNotificacionLeida,

    // Acciones - Herramientas
    cargarHerramientas,

    // Acciones - Contexto
    setProyectoContexto,
    recuperarProyectoContexto,
    setVistaActual,

    // Acciones - Feedback
    enviarFeedback,

    // Limpiar
    limpiar,
  }
})
