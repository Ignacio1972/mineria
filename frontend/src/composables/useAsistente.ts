/**
 * Composable para el Asistente IA.
 *
 * Proporciona una interfaz simplificada para interactuar con el asistente,
 * incluyendo WebSocket para comunicacion en tiempo real.
 */
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useAsistenteStore } from '@/stores/asistente'
import { useRoute } from 'vue-router'
import type { MensajeResponse, ChatResponse } from '@/types'

// Configuracion WebSocket
const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:9001/api/v1/asistente/ws'
const RECONNECT_INTERVAL = 3000
const MAX_RECONNECT_ATTEMPTS = 5
const HEARTBEAT_INTERVAL = 30000

export function useAsistente() {
  const store = useAsistenteStore()
  const route = useRoute()

  // WebSocket
  const ws = ref<WebSocket | null>(null)
  const wsConectado = ref(false)
  const wsReconectando = ref(false)
  const reconnectAttempts = ref(0)

  // Input del chat
  const inputMensaje = ref('')
  const inputRef = ref<HTMLInputElement | null>(null)

  // Scroll
  const mensajesContainerRef = ref<HTMLElement | null>(null)

  // Heartbeat
  let heartbeatTimer: ReturnType<typeof setInterval> | null = null

  // ==========================================================================
  // Computed
  // ==========================================================================

  const mensajes = computed(() => store.mensajes)
  const cargando = computed(() => store.cargando)
  const enviando = computed(() => store.enviando)
  const error = computed(() => store.error)
  const escribiendo = computed(() => store.estado.escribiendo)
  const accionPendiente = computed(() => store.accionActual)
  const tieneAccionPendiente = computed(() => store.accionActual !== null)
  const conversacionId = computed(() => store.conversacionActual?.id)
  const notificaciones = computed(() => store.notificaciones)
  const tieneNotificaciones = computed(() => store.tieneNotificaciones)

  // ==========================================================================
  // WebSocket
  // ==========================================================================

  function conectarWebSocket(): void {
    if (ws.value?.readyState === WebSocket.OPEN) return

    try {
      const url = `${WS_BASE_URL}/${store.sessionId}`
      ws.value = new WebSocket(url)

      ws.value.onopen = () => {
        wsConectado.value = true
        wsReconectando.value = false
        reconnectAttempts.value = 0
        iniciarHeartbeat()
        console.log('WebSocket conectado')
      }

      ws.value.onclose = () => {
        wsConectado.value = false
        detenerHeartbeat()

        // Intentar reconectar
        if (reconnectAttempts.value < MAX_RECONNECT_ATTEMPTS) {
          wsReconectando.value = true
          setTimeout(() => {
            reconnectAttempts.value++
            conectarWebSocket()
          }, RECONNECT_INTERVAL * Math.pow(2, reconnectAttempts.value))
        }
      }

      ws.value.onerror = (event) => {
        console.error('Error WebSocket:', event)
      }

      ws.value.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          manejarMensajeWS(data)
        } catch (e) {
          console.error('Error parsing WS message:', e)
        }
      }
    } catch (e) {
      console.error('Error conectando WebSocket:', e)
    }
  }

  function desconectarWebSocket(): void {
    detenerHeartbeat()
    if (ws.value) {
      ws.value.close()
      ws.value = null
    }
    wsConectado.value = false
  }

  function iniciarHeartbeat(): void {
    heartbeatTimer = setInterval(() => {
      if (ws.value?.readyState === WebSocket.OPEN) {
        ws.value.send(JSON.stringify({ tipo: 'ping' }))
      }
    }, HEARTBEAT_INTERVAL)
  }

  function detenerHeartbeat(): void {
    if (heartbeatTimer) {
      clearInterval(heartbeatTimer)
      heartbeatTimer = null
    }
  }

  function manejarMensajeWS(data: Record<string, unknown>): void {
    const tipo = data.tipo as string

    switch (tipo) {
      case 'pong':
        // Heartbeat response
        break

      case 'typing':
        store.estado.escribiendo = (data.payload as { is_typing: boolean })?.is_typing ?? false
        break

      case 'chat':
        // Mensaje del asistente via WS
        // Se maneja principalmente via REST por ahora
        break

      case 'notificacion':
        store.cargarNotificaciones()
        break

      case 'error':
        console.error('Error WS:', data.payload)
        break
    }
  }

  // ==========================================================================
  // Acciones del Chat
  // ==========================================================================

  /**
   * Envia un mensaje al asistente.
   */
  async function enviarMensaje(): Promise<ChatResponse | null> {
    const mensaje = inputMensaje.value.trim()
    if (!mensaje) return null

    inputMensaje.value = ''
    const respuesta = await store.enviarMensaje(mensaje)

    // Scroll al final
    scrollAlFinal()

    return respuesta
  }

  /**
   * Confirma la accion pendiente actual.
   */
  async function confirmarAccion(confirmada: boolean, comentario?: string): Promise<void> {
    if (!store.accionActual) return
    await store.confirmarAccion(store.accionActual.id, confirmada, comentario)
    scrollAlFinal()
  }

  /**
   * Inicia una nueva conversacion.
   */
  function nuevaConversacion(): void {
    store.nuevaConversacion()
    inputMensaje.value = ''
  }

  // ==========================================================================
  // UI Helpers
  // ==========================================================================

  /**
   * Hace scroll al final del contenedor de mensajes.
   */
  function scrollAlFinal(): void {
    setTimeout(() => {
      if (mensajesContainerRef.value) {
        mensajesContainerRef.value.scrollTop = mensajesContainerRef.value.scrollHeight
      }
    }, 100)
  }

  /**
   * Enfoca el input de mensaje.
   */
  function enfocarInput(): void {
    inputRef.value?.focus()
  }

  /**
   * Maneja el evento de tecla en el input.
   */
  function onKeyDown(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      enviarMensaje()
    }
  }

  /**
   * Copia el contenido de un mensaje al portapapeles.
   */
  async function copiarMensaje(mensaje: MensajeResponse): Promise<void> {
    try {
      await navigator.clipboard.writeText(mensaje.contenido)
    } catch (e) {
      console.error('Error copiando mensaje:', e)
    }
  }

  /**
   * Envia feedback positivo sobre un mensaje.
   */
  async function darLike(mensaje: MensajeResponse): Promise<void> {
    await store.enviarFeedback(mensaje.id, true)
  }

  /**
   * Envia feedback negativo sobre un mensaje.
   */
  async function darDislike(mensaje: MensajeResponse): Promise<void> {
    await store.enviarFeedback(mensaje.id, false)
  }

  // ==========================================================================
  // Contexto
  // ==========================================================================

  /**
   * Actualiza el contexto basado en la ruta actual.
   */
  function actualizarContexto(): void {
    const path = route.path

    // Detectar vista actual
    if (path.includes('/proyectos/') && path.includes('/mapa')) {
      store.setVistaActual('mapa')
    } else if (path.includes('/proyectos/') && path.includes('/analisis')) {
      store.setVistaActual('analisis')
    } else if (path.includes('/proyectos/')) {
      store.setVistaActual('proyecto')
    } else if (path.includes('/clientes')) {
      store.setVistaActual('clientes')
    } else if (path.includes('/corpus')) {
      store.setVistaActual('corpus')
    } else {
      store.setVistaActual('dashboard')
    }

    // Detectar proyecto de contexto
    const proyectoMatch = path.match(/\/proyectos\/(\d+)/)
    if (proyectoMatch && proyectoMatch[1]) {
      store.setProyectoContexto(parseInt(proyectoMatch[1]))
    } else {
      store.setProyectoContexto(null)
    }
  }

  // ==========================================================================
  // Lifecycle
  // ==========================================================================

  onMounted(async () => {
    // Cargar datos iniciales
    await Promise.all([
      store.cargarConversaciones(),
      store.cargarNotificaciones(),
      store.cargarHerramientas(),
    ])

    // Actualizar contexto
    actualizarContexto()

    // Conectar WebSocket (opcional, para notificaciones en tiempo real)
    // conectarWebSocket()
  })

  onUnmounted(() => {
    desconectarWebSocket()
  })

  // Watch para actualizar contexto cuando cambia la ruta
  watch(() => route.path, () => {
    actualizarContexto()
  })

  // ==========================================================================
  // Return
  // ==========================================================================

  return {
    // Estado
    mensajes,
    cargando,
    enviando,
    error,
    escribiendo,
    accionPendiente,
    tieneAccionPendiente,
    conversacionId,
    notificaciones,
    tieneNotificaciones,
    wsConectado,

    // Input
    inputMensaje,
    inputRef,
    mensajesContainerRef,

    // Acciones
    enviarMensaje,
    confirmarAccion,
    nuevaConversacion,
    scrollAlFinal,
    enfocarInput,
    onKeyDown,
    copiarMensaje,
    darLike,
    darDislike,

    // WebSocket
    conectarWebSocket,
    desconectarWebSocket,

    // Store completo para acceso avanzado
    store,
  }
}

export default useAsistente
