<script setup lang="ts">
import { computed, nextTick, watch, ref } from 'vue'
import type { MensajeResponse } from '@/types'

interface Props {
  mensajes: MensajeResponse[]
  escribiendo?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  escribiendo: false,
})

const containerRef = ref<HTMLElement | null>(null)

const mensajesOrdenados = computed(() => {
  return [...props.mensajes].sort(
    (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
  )
})

function formatearHora(fecha: string): string {
  return new Date(fecha).toLocaleTimeString('es-CL', {
    hour: '2-digit',
    minute: '2-digit',
  })
}

function scrollToBottom() {
  nextTick(() => {
    if (containerRef.value) {
      containerRef.value.scrollTop = containerRef.value.scrollHeight
    }
  })
}

watch(
  () => props.mensajes.length,
  () => scrollToBottom(),
  { immediate: true }
)

watch(
  () => props.escribiendo,
  (val) => {
    if (val) scrollToBottom()
  }
)
</script>

<template>
  <div ref="containerRef" class="flex-1 overflow-y-auto p-4 space-y-4">
    <!-- Mensaje de bienvenida si no hay mensajes -->
    <div v-if="mensajesOrdenados.length === 0" class="flex flex-col items-center justify-center h-full text-center">
      <div class="bg-primary/10 rounded-full p-6 mb-4">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
      </div>
      <h3 class="text-lg font-semibold mb-2">Asistente de Prefactibilidad</h3>
      <p class="text-base-content/60 max-w-md">
        Soy tu asistente para el analisis de proyectos mineros. Puedo ayudarte con:
      </p>
      <ul class="text-sm text-base-content/60 mt-3 space-y-1 text-left">
        <li class="flex items-center gap-2">
          <span class="text-success">*</span>
          Consultas sobre normativa ambiental (Ley 19.300, DS 40)
        </li>
        <li class="flex items-center gap-2">
          <span class="text-success">*</span>
          Explicacion de clasificaciones DIA/EIA
        </li>
        <li class="flex items-center gap-2">
          <span class="text-success">*</span>
          Creacion y analisis de proyectos
        </li>
        <li class="flex items-center gap-2">
          <span class="text-success">*</span>
          Busqueda en el corpus legal
        </li>
      </ul>
    </div>

    <!-- Lista de mensajes -->
    <template v-for="mensaje in mensajesOrdenados" :key="mensaje.id">
      <!-- Mensaje del usuario -->
      <div v-if="mensaje.rol === 'user'" class="chat chat-end">
        <div class="chat-bubble chat-bubble-primary">
          {{ mensaje.contenido }}
        </div>
        <div class="chat-footer opacity-50 text-xs">
          {{ formatearHora(mensaje.created_at) }}
        </div>
      </div>

      <!-- Mensaje del asistente -->
      <div v-else-if="mensaje.rol === 'assistant'" class="chat chat-start">
        <div class="chat-image avatar">
          <div class="w-10 rounded-full bg-secondary flex items-center justify-center">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-secondary-content" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          </div>
        </div>
        <div class="chat-bubble chat-bubble-secondary">
          <div class="prose prose-sm max-w-none" v-html="mensaje.contenido.replace(/\n/g, '<br>')"></div>

          <!-- Fuentes citadas -->
          <div v-if="mensaje.fuentes && mensaje.fuentes.length > 0" class="mt-3 pt-3 border-t border-base-content/20">
            <p class="text-xs font-semibold mb-2">Fuentes:</p>
            <div class="space-y-1">
              <div
                v-for="(fuente, idx) in mensaje.fuentes"
                :key="idx"
                class="text-xs bg-base-content/10 rounded px-2 py-1 flex items-center justify-between gap-2"
              >
                <div class="flex-1 min-w-0">
                  <!-- Titulo clickeable si hay documento_id -->
                  <router-link
                    v-if="fuente.documento_id"
                    :to="{ path: '/corpus', query: { doc: fuente.documento_id } }"
                    class="font-medium text-primary hover:underline"
                  >
                    {{ fuente.titulo }}
                  </router-link>
                  <span v-else class="font-medium">{{ fuente.titulo }}</span>
                  <span v-if="fuente.referencia" class="opacity-70"> - {{ fuente.referencia }}</span>
                </div>
                <!-- Boton descargar PDF -->
                <a
                  v-if="fuente.url_descarga"
                  :href="fuente.url_descarga"
                  target="_blank"
                  class="btn btn-ghost btn-xs shrink-0"
                  title="Descargar PDF"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </a>
              </div>
            </div>
          </div>

          <!-- Tool calls (si existen) -->
          <div v-if="mensaje.tool_calls && mensaje.tool_calls.length > 0" class="mt-2">
            <div
              v-for="tool in mensaje.tool_calls"
              :key="tool.id"
              class="flex items-center gap-2 text-xs opacity-70"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              <span>{{ tool.name }}</span>
            </div>
          </div>
        </div>
        <div class="chat-footer opacity-50 text-xs flex items-center gap-2">
          {{ formatearHora(mensaje.created_at) }}
          <span v-if="mensaje.tokens_output" class="opacity-50">
            ({{ mensaje.tokens_output }} tokens)
          </span>
        </div>
      </div>

      <!-- Mensaje del sistema/tool -->
      <div v-else class="flex justify-center">
        <div class="badge badge-ghost gap-2 py-3">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {{ mensaje.contenido }}
        </div>
      </div>
    </template>

    <!-- Indicador de escritura -->
    <div v-if="escribiendo" class="chat chat-start">
      <div class="chat-image avatar">
        <div class="w-10 rounded-full bg-secondary flex items-center justify-center">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-secondary-content" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
        </div>
      </div>
      <div class="chat-bubble chat-bubble-secondary">
        <span class="loading loading-dots loading-sm"></span>
      </div>
    </div>
  </div>
</template>
