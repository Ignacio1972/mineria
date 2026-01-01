<script setup lang="ts">
import { ref, computed, watch } from 'vue'

interface Props {
  enviando?: boolean
  disabled?: boolean
  placeholder?: string
  sugerencias?: string[]
}

const props = withDefaults(defineProps<Props>(), {
  enviando: false,
  disabled: false,
  placeholder: 'Escribe tu mensaje...',
  sugerencias: () => [],
})

const emit = defineEmits<{
  (e: 'enviar', mensaje: string): void
  (e: 'seleccionar-sugerencia', sugerencia: string): void
}>()

const mensaje = ref('')
const textareaRef = ref<HTMLTextAreaElement | null>(null)

const puedeEnviar = computed(() => {
  return mensaje.value.trim().length > 0 && !props.enviando && !props.disabled
})

function enviar() {
  if (!puedeEnviar.value) return

  emit('enviar', mensaje.value.trim())
  mensaje.value = ''

  // Reset altura del textarea
  if (textareaRef.value) {
    textareaRef.value.style.height = 'auto'
  }
}

function handleKeydown(event: KeyboardEvent) {
  // Enter sin Shift envia el mensaje
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    enviar()
  }
}

function seleccionarSugerencia(sugerencia: string) {
  mensaje.value = sugerencia
  emit('seleccionar-sugerencia', sugerencia)
  enviar()
}

function autoResize() {
  if (textareaRef.value) {
    textareaRef.value.style.height = 'auto'
    textareaRef.value.style.height = `${Math.min(textareaRef.value.scrollHeight, 150)}px`
  }
}

watch(mensaje, () => {
  autoResize()
})

// Ejemplos de consultas
const ejemplos = [
  '¿Que es el Art. 11 de la Ley 19.300?',
  '¿Cuando un proyecto requiere EIA?',
  'Crea un proyecto de prueba en Atacama',
  '¿Que capas GIS estan disponibles?',
]
</script>

<template>
  <div class="border-t border-base-300 bg-base-100 p-4">
    <!-- Sugerencias -->
    <div v-if="sugerencias.length > 0" class="mb-3">
      <p class="text-xs text-base-content/60 mb-2">Sugerencias:</p>
      <div class="flex flex-wrap gap-2">
        <button
          v-for="(sugerencia, idx) in sugerencias"
          :key="idx"
          class="btn btn-xs btn-outline"
          :disabled="enviando"
          @click="seleccionarSugerencia(sugerencia)"
        >
          {{ sugerencia }}
        </button>
      </div>
    </div>

    <!-- Ejemplos cuando no hay mensajes -->
    <div v-if="sugerencias.length === 0 && !mensaje" class="mb-3">
      <p class="text-xs text-base-content/60 mb-2">Prueba con:</p>
      <div class="flex flex-wrap gap-2">
        <button
          v-for="(ejemplo, idx) in ejemplos"
          :key="idx"
          class="btn btn-xs btn-ghost"
          :disabled="enviando"
          @click="seleccionarSugerencia(ejemplo)"
        >
          {{ ejemplo }}
        </button>
      </div>
    </div>

    <!-- Area de entrada -->
    <div class="flex gap-2 items-end">
      <div class="flex-1">
        <textarea
          ref="textareaRef"
          v-model="mensaje"
          :placeholder="placeholder"
          :disabled="disabled || enviando"
          class="textarea textarea-bordered w-full resize-none min-h-[48px] max-h-[150px]"
          rows="1"
          @keydown="handleKeydown"
        ></textarea>
      </div>

      <button
        class="btn btn-primary"
        :class="{ 'loading': enviando }"
        :disabled="!puedeEnviar"
        @click="enviar"
      >
        <svg v-if="!enviando" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
        </svg>
        <span class="sr-only">Enviar</span>
      </button>
    </div>

    <!-- Indicador de estado -->
    <div v-if="enviando" class="mt-2 flex items-center gap-2 text-xs text-base-content/60">
      <span class="loading loading-spinner loading-xs"></span>
      Procesando...
    </div>

    <!-- Mensaje de ayuda -->
    <p class="text-xs text-base-content/40 mt-2">
      Presiona Enter para enviar, Shift+Enter para nueva linea
    </p>
  </div>
</template>
