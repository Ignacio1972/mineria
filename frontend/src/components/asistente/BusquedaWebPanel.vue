<script setup lang="ts">
import { ref, computed } from 'vue'
import { asistenteService } from '@/services/asistente'
import type { BusquedaWebResponse, ModoBusquedaWeb, FuenteWeb } from '@/types'

const emit = defineEmits<{
  (e: 'volver-chat'): void
}>()

// Estado
const query = ref('')
const modo = ref<ModoBusquedaWeb>('chat')
const contextoChile = ref(true)
const buscando = ref(false)
const resultado = ref<BusquedaWebResponse | null>(null)
const error = ref<string | null>(null)
const perplexityHabilitado = ref<boolean | null>(null)

// Computed
const puedeEnviar = computed(() => query.value.trim().length >= 3 && !buscando.value)

const modos: { value: ModoBusquedaWeb; label: string; desc: string }[] = [
  { value: 'chat', label: 'Chat', desc: 'Respuestas rápidas' },
  { value: 'research', label: 'Research', desc: 'Investigación profunda' },
  { value: 'reasoning', label: 'Reasoning', desc: 'Análisis lógico' },
]

// Métodos
async function buscar() {
  if (!puedeEnviar.value) return

  buscando.value = true
  error.value = null
  resultado.value = null

  try {
    resultado.value = await asistenteService.buscarWeb({
      query: query.value,
      modo: modo.value,
      contexto_chile: contextoChile.value,
    })
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } }; message?: string }
    error.value = err.response?.data?.detail || err.message || 'Error en búsqueda'
  } finally {
    buscando.value = false
  }
}

async function verificarPerplexity() {
  try {
    const info = await asistenteService.obtenerRouterInfo()
    perplexityHabilitado.value = info.perplexity_habilitado
  } catch {
    perplexityHabilitado.value = false
  }
}

function limpiar() {
  query.value = ''
  resultado.value = null
  error.value = null
}

function abrirFuente(fuente: FuenteWeb) {
  window.open(fuente.url, '_blank')
}

function formatearRespuesta(texto: string): string {
  return texto
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br>')
    .replace(/^/, '<p>')
    .replace(/$/, '</p>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
}

// Cargar estado inicial
verificarPerplexity()
</script>

<template>
  <div class="bg-base-200 rounded-lg flex flex-col h-full">
    <!-- Header compacto -->
    <div class="bg-primary text-primary-content p-2 flex items-center justify-between shrink-0 rounded-t-lg">
      <div class="flex items-center gap-2">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <span class="font-semibold text-sm">Búsqueda Web</span>
        <div
          v-if="perplexityHabilitado !== null"
          class="badge badge-xs"
          :class="perplexityHabilitado ? 'badge-success' : 'badge-warning'"
        >
          {{ perplexityHabilitado ? 'Perplexity' : 'Claude' }}
        </div>
      </div>
      <div class="flex items-center gap-1">
        <button
          v-if="resultado"
          class="btn btn-ghost btn-xs text-primary-content"
          @click="limpiar"
        >
          Limpiar
        </button>
        <button
          class="btn btn-ghost btn-xs text-primary-content gap-1"
          title="Volver al Chat IA"
          @click="emit('volver-chat')"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
          <span class="text-xs">Chat</span>
        </button>
      </div>
    </div>

    <!-- Contenido -->
    <div class="p-4 flex-1 flex flex-col overflow-hidden">

    <!-- Formulario -->
    <div class="space-y-3 shrink-0">
      <!-- Query input -->
      <div class="form-control">
        <textarea
          v-model="query"
          class="textarea textarea-bordered w-full"
          placeholder="Ej: ¿Hay cambios recientes en la Ley 19.300?"
          rows="2"
          :disabled="buscando"
          @keydown.ctrl.enter="buscar"
        ></textarea>
      </div>

      <!-- Opciones -->
      <div class="flex flex-wrap items-center gap-4">
        <!-- Modo -->
        <div class="flex items-center gap-2">
          <span class="text-sm text-base-content/70">Modo:</span>
          <div class="join">
            <button
              v-for="m in modos"
              :key="m.value"
              class="btn btn-xs join-item"
              :class="{ 'btn-primary': modo === m.value }"
              :disabled="buscando"
              :title="m.desc"
              @click="modo = m.value"
            >
              {{ m.label }}
            </button>
          </div>
        </div>

        <!-- Contexto Chile -->
        <label class="flex items-center gap-2 cursor-pointer">
          <input
            v-model="contextoChile"
            type="checkbox"
            class="checkbox checkbox-sm checkbox-primary"
            :disabled="buscando"
          />
          <span class="text-sm">Contexto normativa chilena</span>
        </label>

        <!-- Botón buscar -->
        <button
          class="btn btn-primary btn-sm ml-auto"
          :disabled="!puedeEnviar"
          @click="buscar"
        >
          <span v-if="buscando" class="loading loading-spinner loading-xs"></span>
          <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          {{ buscando ? 'Buscando...' : 'Buscar' }}
        </button>
      </div>
    </div>

    <!-- Error -->
    <div v-if="error" class="alert alert-error mt-4 shrink-0">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <span>{{ error }}</span>
    </div>

    <!-- Resultado -->
    <div v-if="resultado" class="mt-4 space-y-4 flex-1 overflow-y-auto min-h-0">
      <!-- Respuesta -->
      <div class="bg-base-100 rounded-lg p-4">
        <div class="flex items-center gap-2 mb-2 text-sm text-base-content/60">
          <span class="badge badge-ghost badge-sm">{{ resultado.proveedor }}</span>
          <span class="badge badge-ghost badge-sm">{{ resultado.modelo }}</span>
          <span>{{ resultado.tokens_usados }} tokens</span>
        </div>
        <div class="prose prose-sm max-w-none" v-html="formatearRespuesta(resultado.respuesta)"></div>
      </div>

      <!-- Fuentes -->
      <div v-if="resultado.fuentes.length > 0">
        <h4 class="text-sm font-medium mb-2 flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
          </svg>
          Fuentes ({{ resultado.fuentes.length }})
        </h4>
        <div class="space-y-2">
          <div
            v-for="(fuente, idx) in resultado.fuentes"
            :key="idx"
            class="bg-base-100 rounded p-3 cursor-pointer hover:bg-base-300 transition-colors"
            @click="abrirFuente(fuente)"
          >
            <div class="flex items-start gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mt-0.5 shrink-0 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
              <div class="flex-1 min-w-0">
                <p class="font-medium text-sm truncate">{{ fuente.titulo }}</p>
                <p class="text-xs text-base-content/60 truncate">{{ fuente.url }}</p>
                <p v-if="fuente.fragmento" class="text-xs mt-1 line-clamp-2">{{ fuente.fragmento }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Hint -->
    <p v-if="!resultado && !error" class="text-xs text-base-content/50 mt-3 shrink-0">
      Presiona Ctrl+Enter para buscar. Usa modo "Research" para investigaciones profundas.
    </p>
    </div>
  </div>
</template>
