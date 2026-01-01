<script setup lang="ts">
import { ref, computed, onUnmounted, watch } from 'vue'

const props = defineProps<{
  documentoId: number
  nombreArchivo: string
  tipoArchivo?: string
}>()

const emit = defineEmits<{
  (e: 'cerrar'): void
  (e: 'descargar'): void
}>()

const cargando = ref(true)
const error = ref<string | null>(null)
const pdfUrl = ref<string | null>(null)
const zoom = ref(100)

// Construir URL del archivo
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

const archivoUrl = computed(() => {
  return `${API_BASE_URL}/corpus/${props.documentoId}/archivo`
})

// Determinar si es PDF
const esPdf = computed(() => {
  return props.tipoArchivo?.toLowerCase() === 'application/pdf' ||
         props.nombreArchivo.toLowerCase().endsWith('.pdf')
})

// Cargar PDF como blob URL para el iframe
async function cargarPdf() {
  if (!esPdf.value) {
    error.value = 'Este archivo no es un PDF'
    cargando.value = false
    return
  }

  try {
    const response = await fetch(archivoUrl.value)

    if (!response.ok) {
      throw new Error(`Error ${response.status}: ${response.statusText}`)
    }

    const blob = await response.blob()

    // Verificar que sea PDF
    if (blob.type !== 'application/pdf') {
      throw new Error('El archivo descargado no es un PDF válido')
    }

    pdfUrl.value = URL.createObjectURL(blob)
    error.value = null
  } catch (e) {
    console.error('Error cargando PDF:', e)
    error.value = e instanceof Error ? e.message : 'Error al cargar el PDF'
    pdfUrl.value = null
  } finally {
    cargando.value = false
  }
}

function onIframeLoad() {
  cargando.value = false
}

function onIframeError() {
  cargando.value = false
  error.value = 'Error al renderizar el PDF'
}

function aumentarZoom() {
  if (zoom.value < 200) zoom.value += 25
}

function reducirZoom() {
  if (zoom.value > 50) zoom.value -= 25
}

function resetZoom() {
  zoom.value = 100
}

// Limpiar blob URL al desmontar
onUnmounted(() => {
  if (pdfUrl.value) {
    URL.revokeObjectURL(pdfUrl.value)
  }
})

// Cargar cuando cambia el documento
watch(
  () => props.documentoId,
  () => {
    if (pdfUrl.value) {
      URL.revokeObjectURL(pdfUrl.value)
      pdfUrl.value = null
    }
    cargando.value = true
    error.value = null
    cargarPdf()
  },
  { immediate: true }
)
</script>

<template>
  <div class="pdf-viewer flex flex-col h-full bg-base-200 rounded-lg overflow-hidden">
    <!-- Header -->
    <div class="flex items-center justify-between px-4 py-2 bg-base-300 border-b border-base-content/10">
      <div class="flex items-center gap-2">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-error" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
        </svg>
        <span class="font-medium text-sm truncate max-w-xs">{{ nombreArchivo }}</span>
      </div>

      <div class="flex items-center gap-2">
        <!-- Controles de zoom -->
        <div class="join">
          <button
            class="join-item btn btn-xs btn-ghost"
            :disabled="zoom <= 50"
            @click="reducirZoom"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 12H4" />
            </svg>
          </button>
          <button class="join-item btn btn-xs btn-ghost" @click="resetZoom">
            {{ zoom }}%
          </button>
          <button
            class="join-item btn btn-xs btn-ghost"
            :disabled="zoom >= 200"
            @click="aumentarZoom"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
          </button>
        </div>

        <!-- Descargar -->
        <button class="btn btn-xs btn-ghost" @click="emit('descargar')">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
        </button>

        <!-- Cerrar -->
        <button class="btn btn-xs btn-ghost" @click="emit('cerrar')">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Contenido -->
    <div class="flex-1 overflow-auto relative">
      <!-- Loading -->
      <div v-if="cargando" class="absolute inset-0 flex items-center justify-center bg-base-200">
        <div class="text-center">
          <span class="loading loading-spinner loading-lg"></span>
          <p class="mt-2 text-sm opacity-60">Cargando PDF...</p>
        </div>
      </div>

      <!-- Error -->
      <div v-else-if="error" class="absolute inset-0 flex items-center justify-center bg-base-200">
        <div class="text-center p-8">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 mx-auto text-error opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <p class="mt-4 text-lg font-medium">No se pudo cargar el PDF</p>
          <p class="mt-1 text-sm opacity-60">{{ error }}</p>
          <div class="mt-4 flex justify-center gap-2">
            <button class="btn btn-sm btn-ghost" @click="cargarPdf">
              Reintentar
            </button>
            <button class="btn btn-sm btn-primary" @click="emit('descargar')">
              Descargar archivo
            </button>
          </div>
        </div>
      </div>

      <!-- PDF Iframe -->
      <iframe
        v-else-if="pdfUrl"
        :src="pdfUrl"
        class="w-full h-full border-0 transition-transform"
        :style="{ transform: `scale(${zoom / 100})`, transformOrigin: 'top left', width: `${10000 / zoom}%`, height: `${10000 / zoom}%` }"
        @load="onIframeLoad"
        @error="onIframeError"
      ></iframe>

      <!-- No es PDF -->
      <div v-else-if="!esPdf" class="absolute inset-0 flex items-center justify-center bg-base-200">
        <div class="text-center p-8">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 mx-auto opacity-30" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <p class="mt-4 text-lg font-medium">Vista previa no disponible</p>
          <p class="mt-1 text-sm opacity-60">
            Este tipo de archivo ({{ tipoArchivo || 'desconocido' }}) no puede visualizarse en el navegador
          </p>
          <button class="btn btn-primary mt-4" @click="emit('descargar')">
            Descargar archivo
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.pdf-viewer {
  min-height: 400px;
}
</style>
