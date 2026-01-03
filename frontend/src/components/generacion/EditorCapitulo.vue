<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useGeneracionEiaStore } from '@/stores/generacionEia'
import { storeToRefs } from 'pinia'
import { CAPITULOS_EIA } from '@/types/generacionEia'

const props = defineProps<{
  proyectoId: number
  capituloNumero: number
}>()

const emit = defineEmits<{
  (e: 'guardado'): void
}>()

const store = useGeneracionEiaStore()
const {
  capituloActual,
  guardando,
  generandoCapitulo,
  contenidoSinGuardar,
} = storeToRefs(store)

const contenidoLocal = ref('')
const modoVista = ref<'editor' | 'preview' | 'split'>('split')
const mostrarModalRegenerar = ref(false)
const instruccionesRegenerar = ref('')

// Titulo del capitulo
const tituloCapitulo = computed(() => {
  return CAPITULOS_EIA[props.capituloNumero] || `Capitulo ${props.capituloNumero}`
})

// Cargar contenido cuando cambia el capitulo
watch(
  () => [props.capituloNumero, capituloActual.value],
  () => {
    if (capituloActual.value) {
      contenidoLocal.value = capituloActual.value.contenido || ''
    } else {
      contenidoLocal.value = ''
    }
  },
  { immediate: true }
)

// Marcar cambios sin guardar
watch(contenidoLocal, (nuevo, anterior) => {
  if (anterior !== undefined && nuevo !== (capituloActual.value?.contenido || '')) {
    store.marcarSinGuardar()
  }
})

// Estadisticas del contenido
const estadisticas = computed(() => {
  const texto = contenidoLocal.value
  const palabras = texto.trim() ? texto.trim().split(/\s+/).length : 0
  const caracteres = texto.length
  const lineas = texto.split('\n').length
  return { palabras, caracteres, lineas }
})

// Acciones
async function guardarContenido() {
  try {
    await store.actualizarCapitulo(props.capituloNumero, contenidoLocal.value)
    emit('guardado')
  } catch (e) {
    console.error('Error guardando contenido:', e)
  }
}

async function regenerarCapitulo() {
  mostrarModalRegenerar.value = false
  try {
    await store.generarCapitulo(
      props.capituloNumero,
      instruccionesRegenerar.value || undefined,
      true
    )
    instruccionesRegenerar.value = ''
  } catch (e) {
    console.error('Error regenerando capitulo:', e)
  }
}

function abrirModalRegenerar() {
  instruccionesRegenerar.value = ''
  mostrarModalRegenerar.value = true
}

// Convertir markdown basico a HTML para preview
function renderMarkdown(texto: string): string {
  if (!texto) return '<p class="opacity-50">Sin contenido</p>'

  let html = texto
    // Escapar HTML
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    // Headers
    .replace(/^### (.*$)/gim, '<h3 class="text-lg font-semibold mt-4 mb-2">$1</h3>')
    .replace(/^## (.*$)/gim, '<h2 class="text-xl font-bold mt-6 mb-3">$1</h2>')
    .replace(/^# (.*$)/gim, '<h1 class="text-2xl font-bold mt-8 mb-4">$1</h1>')
    // Bold
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    // Italic
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    // Lists
    .replace(/^\s*-\s+(.*$)/gim, '<li class="ml-4">$1</li>')
    .replace(/^\s*\d+\.\s+(.*$)/gim, '<li class="ml-4 list-decimal">$1</li>')
    // Paragraphs (double newline)
    .replace(/\n\n/g, '</p><p class="mb-3">')
    // Single newline to br
    .replace(/\n/g, '<br/>')

  return `<p class="mb-3">${html}</p>`
}
</script>

<template>
  <div class="editor-capitulo h-full flex flex-col">
    <!-- Header del editor -->
    <div class="flex items-center justify-between mb-3">
      <div>
        <h3 class="font-bold">{{ tituloCapitulo }}</h3>
        <div class="text-xs opacity-60">
          {{ estadisticas.palabras }} palabras -
          {{ estadisticas.caracteres }} caracteres -
          {{ estadisticas.lineas }} lineas
        </div>
      </div>

      <div class="flex items-center gap-2">
        <!-- Toggle modo vista -->
        <div class="join">
          <button
            class="join-item btn btn-xs"
            :class="{ 'btn-active': modoVista === 'editor' }"
            @click="modoVista = 'editor'"
            title="Solo editor"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
          </button>
          <button
            class="join-item btn btn-xs"
            :class="{ 'btn-active': modoVista === 'split' }"
            @click="modoVista = 'split'"
            title="Editor y preview"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7" />
            </svg>
          </button>
          <button
            class="join-item btn btn-xs"
            :class="{ 'btn-active': modoVista === 'preview' }"
            @click="modoVista = 'preview'"
            title="Solo preview"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
          </button>
        </div>

        <!-- Botones de accion -->
        <button
          class="btn btn-outline btn-xs"
          :disabled="generandoCapitulo === capituloNumero"
          @click="abrirModalRegenerar"
        >
          <span v-if="generandoCapitulo === capituloNumero" class="loading loading-spinner loading-xs"></span>
          <span v-else>Regenerar</span>
        </button>

        <button
          class="btn btn-primary btn-xs"
          :disabled="guardando || !contenidoSinGuardar"
          @click="guardarContenido"
        >
          <span v-if="guardando" class="loading loading-spinner loading-xs"></span>
          <span v-else>Guardar</span>
        </button>
      </div>
    </div>

    <!-- Indicador de cambios sin guardar -->
    <div v-if="contenidoSinGuardar" class="alert alert-warning py-1 px-3 mb-2 text-xs">
      Hay cambios sin guardar
    </div>

    <!-- Area de edicion -->
    <div class="flex-1 overflow-hidden flex gap-2" :class="{ 'flex-col': modoVista !== 'split' }">
      <!-- Editor -->
      <div
        v-if="modoVista === 'editor' || modoVista === 'split'"
        class="flex-1 min-h-0"
        :class="{ 'w-1/2': modoVista === 'split' }"
      >
        <textarea
          v-model="contenidoLocal"
          class="textarea textarea-bordered w-full h-full font-mono text-sm resize-none"
          placeholder="Escribe el contenido del capitulo aqui..."
          :disabled="generandoCapitulo === capituloNumero"
        ></textarea>
      </div>

      <!-- Preview -->
      <div
        v-if="modoVista === 'preview' || modoVista === 'split'"
        class="flex-1 min-h-0 overflow-y-auto"
        :class="{ 'w-1/2': modoVista === 'split' }"
      >
        <div
          class="prose prose-sm max-w-none p-4 bg-base-200 rounded-lg h-full"
          v-html="renderMarkdown(contenidoLocal)"
        ></div>
      </div>
    </div>

    <!-- Modal Regenerar -->
    <dialog
      class="modal"
      :class="{ 'modal-open': mostrarModalRegenerar }"
    >
      <div class="modal-box">
        <h3 class="font-bold text-lg mb-4">Regenerar Capitulo</h3>

        <div class="alert alert-warning text-sm mb-4">
          <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-5 w-5" fill="none" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <span>Esto reemplazara el contenido actual del capitulo.</span>
        </div>

        <div class="form-control mb-4">
          <label class="label">
            <span class="label-text">Instrucciones adicionales (opcional)</span>
          </label>
          <textarea
            v-model="instruccionesRegenerar"
            class="textarea textarea-bordered"
            rows="3"
            placeholder="Ej: Enfocarse mas en los impactos al agua, incluir referencias a normativa especifica..."
          ></textarea>
        </div>

        <div class="modal-action">
          <button class="btn btn-ghost" @click="mostrarModalRegenerar = false">
            Cancelar
          </button>
          <button
            class="btn btn-warning"
            :disabled="generandoCapitulo === capituloNumero"
            @click="regenerarCapitulo"
          >
            <span v-if="generandoCapitulo === capituloNumero" class="loading loading-spinner loading-sm"></span>
            <span v-else>Regenerar</span>
          </button>
        </div>
      </div>
      <form method="dialog" class="modal-backdrop">
        <button @click="mostrarModalRegenerar = false">close</button>
      </form>
    </dialog>
  </div>
</template>

<style scoped>
.editor-capitulo {
  min-height: 400px;
}

.prose h1, .prose h2, .prose h3 {
  margin-top: 1rem;
  margin-bottom: 0.5rem;
}

.prose p {
  margin-bottom: 0.75rem;
}

.prose li {
  margin-left: 1.5rem;
}
</style>
