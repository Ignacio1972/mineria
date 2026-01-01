<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAsistenteStore } from '@/stores/asistente'
import { storeToRefs } from 'pinia'
import MessageList from '@/components/asistente/MessageList.vue'
import InputArea from '@/components/asistente/InputArea.vue'
import ActionPanel from '@/components/asistente/ActionPanel.vue'
import ConfirmDialog from '@/components/asistente/ConfirmDialog.vue'
import BusquedaWebPanel from '@/components/asistente/BusquedaWebPanel.vue'
import type { NotificacionProactiva } from '@/types'

const router = useRouter()
const store = useAsistenteStore()

const {
  mensajes,
  conversaciones,
  conversacionActual,
  estado,
  enviando,
  cargando,
  accionActual,
  accionesPendientes,
  notificaciones,
  herramientas,
  error,
} = storeToRefs(store)

// Estado local
const panelHistorial = ref(true)
const panelBusquedaWeb = ref(false)
const dialogoConfirmacion = ref(false)
const procesandoConfirmacion = ref(false)
const sugerenciasActuales = ref<string[]>([])

// Computed
const conversacionesOrdenadas = computed(() => {
  return [...conversaciones.value].sort(
    (a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
  )
})

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
    router.push(notificacion.accion_sugerida)
  }
  store.marcarNotificacionLeida(notificacion.id, 'vista')
}

function handleDescartarNotificacion(notificacionId: string) {
  store.marcarNotificacionLeida(notificacionId, 'descartada')
}

// Seleccionar conversacion
async function seleccionarConversacion(conversacionId: string) {
  await store.cargarConversacion(conversacionId)
  sugerenciasActuales.value = []
}

// Nueva conversacion
function nuevaConversacion() {
  store.nuevaConversacion()
  sugerenciasActuales.value = []
}

// Eliminar conversacion
async function eliminarConversacion(conversacionId: string) {
  if (confirm('¿Estas seguro de eliminar esta conversacion?')) {
    await store.eliminarConversacion(conversacionId)
  }
}

// Formatear fecha
function formatearFecha(fecha: string): string {
  const date = new Date(fecha)
  const hoy = new Date()
  const ayer = new Date(hoy)
  ayer.setDate(ayer.getDate() - 1)

  if (date.toDateString() === hoy.toDateString()) {
    return 'Hoy ' + date.toLocaleTimeString('es-CL', { hour: '2-digit', minute: '2-digit' })
  } else if (date.toDateString() === ayer.toDateString()) {
    return 'Ayer ' + date.toLocaleTimeString('es-CL', { hour: '2-digit', minute: '2-digit' })
  }
  return date.toLocaleDateString('es-CL', { day: '2-digit', month: 'short' })
}

// Cargar datos iniciales
onMounted(async () => {
  store.setVistaActual('asistente')
  await Promise.all([
    store.cargarConversaciones(),
    store.cargarNotificaciones(),
    store.cargarHerramientas(),
  ])
})
</script>

<template>
  <div class="h-[calc(100vh-4rem)] flex">
    <!-- Panel lateral: Historial de conversaciones -->
    <aside
      class="bg-base-200 flex flex-col transition-all duration-300 shrink-0"
      :class="{ 'w-72': panelHistorial, 'w-0 overflow-hidden': !panelHistorial }"
    >
      <!-- Header del panel -->
      <div class="p-4 border-b border-base-300 flex items-center justify-between">
        <h2 class="font-semibold">Conversaciones</h2>
        <button
          class="btn btn-sm btn-primary"
          @click="nuevaConversacion"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          Nueva
        </button>
      </div>

      <!-- Lista de conversaciones -->
      <div class="flex-1 overflow-y-auto p-2">
        <div v-if="cargando" class="flex justify-center p-4">
          <span class="loading loading-spinner"></span>
        </div>

        <div v-else-if="conversaciones.length === 0" class="text-center p-4 text-base-content/60">
          <p class="text-sm">No hay conversaciones</p>
          <p class="text-xs mt-1">Inicia una nueva para comenzar</p>
        </div>

        <ul v-else class="space-y-1">
          <li
            v-for="conv in conversacionesOrdenadas"
            :key="conv.id"
            class="rounded-lg cursor-pointer group"
            :class="{
              'bg-primary/10': conversacionActual?.id === conv.id,
              'hover:bg-base-300': conversacionActual?.id !== conv.id,
            }"
          >
            <div
              class="p-3 flex items-start gap-2"
              @click="seleccionarConversacion(conv.id)"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 shrink-0 mt-0.5 text-base-content/60" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>

              <div class="flex-1 min-w-0">
                <p class="text-sm font-medium truncate">
                  {{ conv.titulo || 'Sin titulo' }}
                </p>
                <p class="text-xs text-base-content/60">
                  {{ formatearFecha(conv.updated_at) }}
                  <span class="opacity-50"> - {{ conv.total_mensajes }} msgs</span>
                </p>
              </div>

              <button
                class="btn btn-ghost btn-xs btn-circle opacity-0 group-hover:opacity-100"
                @click.stop="eliminarConversacion(conv.id)"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>
          </li>
        </ul>
      </div>

      <!-- Herramientas disponibles -->
      <div class="p-4 border-t border-base-300">
        <details class="collapse collapse-arrow bg-base-100 rounded-lg">
          <summary class="collapse-title text-sm font-medium py-2 min-h-0">
            Herramientas ({{ herramientas.length }})
          </summary>
          <div class="collapse-content text-xs">
            <ul class="space-y-1 mt-2">
              <li
                v-for="tool in herramientas"
                :key="tool.name"
                class="flex items-center gap-2"
              >
                <span
                  class="w-2 h-2 rounded-full"
                  :class="{
                    'bg-success': !tool.requiere_confirmacion,
                    'bg-warning': tool.requiere_confirmacion,
                  }"
                ></span>
                {{ tool.name }}
              </li>
            </ul>
          </div>
        </details>
      </div>
    </aside>

    <!-- Boton toggle panel lateral -->
    <button
      class="bg-base-300 hover:bg-base-content/20 px-1 flex items-center"
      @click="panelHistorial = !panelHistorial"
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        class="h-4 w-4 transition-transform"
        :class="{ 'rotate-180': !panelHistorial }"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
      </svg>
    </button>

    <!-- Panel principal del chat -->
    <main class="flex-1 flex flex-col bg-base-100 min-w-0">
      <!-- Header del chat -->
      <header class="bg-primary text-primary-content p-4 flex items-center justify-between shrink-0">
        <div class="flex items-center gap-3">
          <div class="bg-primary-content/20 rounded-full p-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          </div>
          <div>
            <h1 class="font-bold text-lg">Asistente de Prefactibilidad</h1>
            <p class="text-sm opacity-80">
              {{ conversacionActual ? conversacionActual.titulo : 'Nueva conversacion' }}
            </p>
          </div>
        </div>

        <div class="flex items-center gap-2">
          <!-- Botón Búsqueda Web -->
          <button
            class="btn btn-ghost btn-sm gap-1"
            :class="{ 'btn-active': panelBusquedaWeb }"
            @click="panelBusquedaWeb = !panelBusquedaWeb"
            title="Búsqueda Web (Perplexity)"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
            </svg>
            <span class="hidden sm:inline">Web</span>
          </button>

          <!-- Indicador de estado -->
          <div class="flex items-center gap-2 text-sm">
            <span
              class="w-2 h-2 rounded-full"
              :class="{
                'bg-success': estado.conectado && !estado.procesando,
                'bg-warning animate-pulse': estado.procesando,
                'bg-error': !estado.conectado,
              }"
            ></span>
            <span class="opacity-80">
              {{ estado.procesando ? 'Procesando...' : estado.conectado ? 'Conectado' : 'Desconectado' }}
            </span>
          </div>

          <!-- Notificaciones -->
          <div v-if="notificaciones.length > 0" class="dropdown dropdown-end">
            <label tabindex="0" class="btn btn-ghost btn-circle">
              <div class="indicator">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                </svg>
                <span class="badge badge-error badge-xs indicator-item">
                  {{ notificaciones.length }}
                </span>
              </div>
            </label>
            <ul tabindex="0" class="dropdown-content z-50 menu shadow-lg bg-base-100 rounded-box w-80 text-base-content">
              <li v-for="notif in notificaciones" :key="notif.id">
                <a @click="handleVerNotificacion(notif)">
                  <div class="flex-1">
                    <p class="text-sm">{{ notif.mensaje }}</p>
                    <p v-if="notif.proyecto_nombre" class="text-xs opacity-60">
                      {{ notif.proyecto_nombre }}
                    </p>
                  </div>
                </a>
              </li>
            </ul>
          </div>
        </div>
      </header>

      <!-- Modo Búsqueda Web - Ocupa todo el espacio -->
      <div
        v-if="panelBusquedaWeb"
        class="flex-1 overflow-hidden p-4"
      >
        <BusquedaWebPanel class="h-full" />
      </div>

      <!-- Modo Chat - Solo visible cuando no está el panel web -->
      <template v-else>
        <!-- Error global -->
        <div v-if="error" class="alert alert-error m-4">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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
          :notificaciones="[]"
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
    </main>

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
