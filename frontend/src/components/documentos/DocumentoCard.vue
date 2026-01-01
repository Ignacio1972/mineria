<script setup lang="ts">
import { computed } from 'vue'
import type { Documento } from '@/types'
import { CATEGORIAS_DOCUMENTO } from '@/types'

const props = defineProps<{
  documento: Documento
  readonly?: boolean
}>()

const emit = defineEmits<{
  descargar: [documento: Documento]
  eliminar: [documento: Documento]
}>()

const categoriaInfo = computed(() =>
  CATEGORIAS_DOCUMENTO.find((c) => c.value === props.documento.categoria)
)

const iconoMime = computed(() => {
  const mime = props.documento.mime_type
  if (mime.startsWith('image/')) return 'image'
  if (mime === 'application/pdf') return 'pdf'
  if (mime.includes('spreadsheet') || mime.includes('excel')) return 'excel'
  if (mime.includes('document') || mime.includes('word')) return 'word'
  if (mime.includes('zip') || mime.includes('compressed')) return 'zip'
  return 'file'
})

const colorCategoria = computed(() => {
  switch (props.documento.categoria) {
    case 'legal':
      return 'badge-primary'
    case 'tecnico':
      return 'badge-secondary'
    case 'ambiental':
      return 'badge-success'
    case 'cartografia':
      return 'badge-info'
    default:
      return 'badge-ghost'
  }
})

function formatTamano(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
}

function formatFecha(fecha: string): string {
  return new Date(fecha).toLocaleDateString('es-CL', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}
</script>

<template>
  <div class="card card-compact bg-base-100 shadow-sm hover:shadow-md transition-shadow">
    <div class="card-body">
      <div class="flex items-start gap-3">
        <!-- Icono de tipo de archivo -->
        <div class="flex-shrink-0">
          <div class="w-10 h-10 rounded-lg bg-base-200 flex items-center justify-center">
            <!-- PDF -->
            <svg v-if="iconoMime === 'pdf'" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-error" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
            </svg>
            <!-- Imagen -->
            <svg v-else-if="iconoMime === 'image'" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-success" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <!-- Excel -->
            <svg v-else-if="iconoMime === 'excel'" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-success" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
            <!-- Word -->
            <svg v-else-if="iconoMime === 'word'" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <!-- Zip -->
            <svg v-else-if="iconoMime === 'zip'" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-warning" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
            </svg>
            <!-- Default -->
            <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 opacity-60" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
            </svg>
          </div>
        </div>

        <!-- Info -->
        <div class="flex-1 min-w-0">
          <h4 class="font-medium truncate" :title="documento.nombre">
            {{ documento.nombre }}
          </h4>
          <p class="text-xs opacity-60 truncate" :title="documento.nombre_original">
            {{ documento.nombre_original }}
          </p>
          <div class="flex items-center gap-2 mt-1">
            <span class="badge badge-xs" :class="colorCategoria">
              {{ categoriaInfo?.label }}
            </span>
            <span class="text-xs opacity-40">{{ formatTamano(documento.tamano_bytes) }}</span>
            <span class="text-xs opacity-40">{{ formatFecha(documento.created_at) }}</span>
          </div>
          <p v-if="documento.descripcion" class="text-xs opacity-60 mt-1 line-clamp-2">
            {{ documento.descripcion }}
          </p>
        </div>

        <!-- Acciones -->
        <div class="flex-shrink-0 flex items-center gap-1">
          <button
            class="btn btn-ghost btn-xs btn-square"
            title="Descargar"
            @click="emit('descargar', documento)"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
          </button>
          <button
            v-if="!readonly"
            class="btn btn-ghost btn-xs btn-square text-error"
            title="Eliminar"
            @click="emit('eliminar', documento)"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
