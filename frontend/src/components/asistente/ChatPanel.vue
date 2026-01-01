<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useAsistenteStore } from '@/stores/asistente'
import { storeToRefs } from 'pinia'
import MessageList from './MessageList.vue'
import InputArea from './InputArea.vue'
import ActionPanel from './ActionPanel.vue'
import ConfirmDialog from './ConfirmDialog.vue'
import type { NotificacionProactiva } from '@/types'

interface Props {
  proyectoId?: number
  vistaActual?: string
  colapsado?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  vistaActual: 'dashboard',
  colapsado: false,
})

const emit = defineEmits<{
  (e: 'toggle-colapso'): void
  (e: 'navegar', ruta: string): void
}>()

const store = useAsistenteStore()
const {
  mensajes,
  estado,
  enviando,
  accionActual,
  accionesPendientes,
  notificaciones,
  error,
} = storeToRefs(store)

// Estado local
const dialogoConfirmacion = ref(false)
const procesandoConfirmacion = ref(false)
const sugerenciasActuales = ref<string[]>([])

// Actualizar contexto cuando cambie el proyecto
watch(
  () => props.proyectoId,
  (newId) => {
    store.setProyectoContexto(newId ?? null)
  },
  { immediate: true }
)

watch(
  () => props.vistaActual,
  (newVista) => {
    store.setVistaActual(newVista)
  },
  { immediate: true }
)

// Manejar envio de mensaje
async function handleEnviarMensaje(mensaje: string) {
  try {
    const respuesta = await store.enviarMensaje(mensaje)
    if (respuesta?.sugerencias) {
      sugerenciasActuales.value = respuesta.sugerencias
    }
  } catch (e) {
    console.error('Error enviando mensaje:', e)
  }
}

// Manejar confirmacion de accion
function handleConfirmarAccion(accionId: string) {
  const accion = accionesPendientes.value.find((a) => a.id === accionId)
  if (accion) {
    store.accionActual = accion
    dialogoConfirmacion.value = true
  }
}

function handleCancelarAccion(accionId: string) {
  confirmarAccion(accionId, false)
}

async function confirmarAccion(accionId: string, confirmada: boolean, comentario?: string) {
  procesandoConfirmacion.value = true
  try {
    await store.confirmarAccion(accionId, confirmada, comentario)
  } catch (e) {
    console.error('Error confirmando accion:', e)
  } finally {
    procesandoConfirmacion.value = false
    dialogoConfirmacion.value = false
  }
}

function handleConfirmarDialogo(comentario?: string) {
  if (accionActual.value) {
    confirmarAccion(accionActual.value.id, true, comentario)
  }
}

function handleCancelarDialogo() {
  if (accionActual.value) {
    confirmarAccion(accionActual.value.id, false)
  }
}

// Manejar notificaciones
function handleVerNotificacion(notificacion: NotificacionProactiva) {
  if (notificacion.accion_sugerida) {
    emit('navegar', notificacion.accion_sugerida)
  }
  store.marcarNotificacionLeida(notificacion.id, 'vista')
}

function handleDescartarNotificacion(notificacionId: string) {
  store.marcarNotificacionLeida(notificacionId, 'descartada')
}

// Nueva conversacion
function nuevaConversacion() {
  store.nuevaConversacion()
  sugerenciasActuales.value = []
}

// Cargar datos iniciales
onMounted(async () => {
  await Promise.all([
    store.cargarConversaciones(),
    store.cargarNotificaciones(),
    store.cargarHerramientas(),
  ])
})
</script>

<template>
  <div
    class="flex flex-col h-full bg-base-100 rounded-lg shadow-lg overflow-hidden"
    :class="{ 'w-80': !colapsado, 'w-12': colapsado }"
  >
    <!-- Header -->
    <div class="bg-primary text-primary-content p-3 flex items-center justify-between shrink-0">
      <div v-if="!colapsado" class="flex items-center gap-2">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
        <span class="font-semibold">Asistente IA</span>

        <!-- Indicador de estado -->
        <span
          class="w-2 h-2 rounded-full"
          :class="{
            'bg-success': estado.conectado && !estado.procesando,
            'bg-warning animate-pulse': estado.procesando,
            'bg-error': !estado.conectado,
          }"
        ></span>
      </div>

      <div class="flex items-center gap-1">
        <!-- Nueva conversacion -->
        <button
          v-if="!colapsado"
          class="btn btn-ghost btn-sm btn-circle text-primary-content"
          title="Nueva conversacion"
          @click="nuevaConversacion"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
        </button>

        <!-- Toggle colapso -->
        <button
          class="btn btn-ghost btn-sm btn-circle text-primary-content"
          :title="colapsado ? 'Expandir' : 'Colapsar'"
          @click="emit('toggle-colapso')"
        >
          <svg v-if="!colapsado" xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 5l7 7-7 7M5 5l7 7-7 7" />
          </svg>
          <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Contenido cuando esta expandido -->
    <template v-if="!colapsado">
      <!-- Error global -->
      <div v-if="error" class="alert alert-error m-2 text-sm">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span>{{ error }}</span>
      </div>

      <!-- Lista de mensajes -->
      <MessageList
        :mensajes="mensajes"
        :escribiendo="estado.escribiendo"
      />

      <!-- Panel de acciones -->
      <ActionPanel
        :acciones-pendientes="accionesPendientes"
        :notificaciones="notificaciones"
        @confirmar-accion="handleConfirmarAccion"
        @cancelar-accion="handleCancelarAccion"
        @ver-notificacion="handleVerNotificacion"
        @descartar-notificacion="handleDescartarNotificacion"
      />

      <!-- Area de entrada -->
      <InputArea
        :enviando="enviando"
        :disabled="!estado.conectado"
        :sugerencias="sugerenciasActuales"
        @enviar="handleEnviarMensaje"
        @seleccionar-sugerencia="(s) => handleEnviarMensaje(s)"
      />
    </template>

    <!-- Contenido cuando esta colapsado -->
    <div v-else class="flex-1 flex flex-col items-center py-4 gap-4">
      <!-- Icono del asistente -->
      <button
        class="btn btn-ghost btn-circle"
        title="Abrir asistente"
        @click="emit('toggle-colapso')"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
      </button>

      <!-- Indicador de notificaciones -->
      <div
        v-if="notificaciones.length > 0"
        class="indicator"
      >
        <span class="indicator-item badge badge-error badge-xs">
          {{ notificaciones.length }}
        </span>
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-base-content/60" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
      </div>
    </div>

    <!-- Dialogo de confirmacion -->
    <ConfirmDialog
      :accion="accionActual"
      :visible="dialogoConfirmacion"
      :procesando="procesandoConfirmacion"
      @confirmar="handleConfirmarDialogo"
      @cancelar="handleCancelarDialogo"
      @cerrar="dialogoConfirmacion = false"
    />
  </div>
</template>
