<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useGeneracionEiaStore } from '@/stores/generacionEia'
import { storeToRefs } from 'pinia'
import {
  FORMATO_EXPORTACION_LABELS,
  type FormatoExportacionEIA,
} from '@/types/generacionEia'

const props = defineProps<{
  proyectoId: number
}>()

const store = useGeneracionEiaStore()
const {
  exportaciones,
  exportando,
  esValido,
} = storeToRefs(store)

const formatoSeleccionado = ref<FormatoExportacionEIA>('pdf')

// Configuracion PDF
const configPDF = ref({
  incluir_portada: true,
  incluir_indice: true,
  incluir_figuras: true,
  incluir_tablas: true,
  tamano_pagina: 'A4',
  orientacion: 'portrait',
})

// Configuracion DOCX
const configDOCX = ref({
  incluir_portada: true,
  incluir_indice: true,
  incluir_figuras: true,
  incluir_tablas: true,
  estilo_documento: 'SEA_Estandar',
})

// Configuracion e-SEIA
const configESEIA = ref({
  incluir_anexos_digitales: true,
  version_esquema: '2.0',
})

// Exportaciones ordenadas por fecha
const exportacionesOrdenadas = computed(() => {
  return [...exportaciones.value].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  )
})

// Configuracion actual segun formato
const configuracionActual = computed(() => {
  switch (formatoSeleccionado.value) {
    case 'pdf':
      return configPDF.value
    case 'docx':
      return configDOCX.value
    case 'eseia_xml':
      return configESEIA.value
    default:
      return {}
  }
})

// Acciones
async function exportarDocumento() {
  try {
    await store.exportarDocumento(formatoSeleccionado.value, configuracionActual.value)
  } catch (e) {
    console.error('Error exportando:', e)
  }
}

function descargarExportacion(exportacionId: number) {
  const url = store.getUrlDescarga(exportacionId)
  window.open(url, '_blank')
}

function formatearFecha(fecha: string): string {
  const d = new Date(fecha)
  return d.toLocaleDateString('es-CL', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function formatearTamano(bytes: number | null | undefined): string {
  if (!bytes) return '-'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function getIconoFormato(formato: FormatoExportacionEIA): string {
  switch (formato) {
    case 'pdf':
      return 'text-red-500'
    case 'docx':
      return 'text-blue-500'
    case 'eseia_xml':
      return 'text-green-500'
    default:
      return ''
  }
}

onMounted(() => {
  store.cargarExportaciones()
})
</script>

<template>
  <div class="exportador-panel p-4">
    <!-- Formulario de exportacion -->
    <div class="card bg-base-100 shadow-sm mb-4">
      <div class="card-body p-4">
        <h3 class="font-bold text-lg mb-4">Exportar Documento</h3>

        <!-- Advertencia si no es valido -->
        <div v-if="!esValido" class="alert alert-warning mb-4">
          <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-5 w-5" fill="none" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <span>El documento tiene errores de validacion. Se recomienda corregirlos antes de exportar.</span>
        </div>

        <!-- Selector de formato -->
        <div class="form-control mb-4">
          <label class="label">
            <span class="label-text font-medium">Formato de exportacion</span>
          </label>
          <div class="flex gap-2">
            <label
              v-for="(label, formato) in FORMATO_EXPORTACION_LABELS"
              :key="formato"
              class="flex-1"
            >
              <input
                v-model="formatoSeleccionado"
                type="radio"
                :value="formato"
                class="hidden peer"
              />
              <div
                class="card bg-base-200 cursor-pointer transition-all peer-checked:ring-2 peer-checked:ring-primary peer-checked:bg-primary/10"
              >
                <div class="card-body p-3 items-center">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    class="h-8 w-8"
                    :class="getIconoFormato(formato as FormatoExportacionEIA)"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <span class="text-sm font-medium">{{ label }}</span>
                </div>
              </div>
            </label>
          </div>
        </div>

        <!-- Opciones PDF -->
        <div v-if="formatoSeleccionado === 'pdf'" class="space-y-2 mb-4">
          <h4 class="text-sm font-medium opacity-70">Opciones PDF</h4>
          <div class="grid grid-cols-2 gap-2">
            <label class="flex items-center gap-2 cursor-pointer">
              <input v-model="configPDF.incluir_portada" type="checkbox" class="checkbox checkbox-sm" />
              <span class="text-sm">Incluir portada</span>
            </label>
            <label class="flex items-center gap-2 cursor-pointer">
              <input v-model="configPDF.incluir_indice" type="checkbox" class="checkbox checkbox-sm" />
              <span class="text-sm">Incluir indice</span>
            </label>
            <label class="flex items-center gap-2 cursor-pointer">
              <input v-model="configPDF.incluir_figuras" type="checkbox" class="checkbox checkbox-sm" />
              <span class="text-sm">Incluir figuras</span>
            </label>
            <label class="flex items-center gap-2 cursor-pointer">
              <input v-model="configPDF.incluir_tablas" type="checkbox" class="checkbox checkbox-sm" />
              <span class="text-sm">Incluir tablas</span>
            </label>
          </div>
          <div class="flex gap-2">
            <select v-model="configPDF.tamano_pagina" class="select select-bordered select-sm">
              <option value="A4">Tamano A4</option>
              <option value="Letter">Tamano Carta</option>
              <option value="Legal">Tamano Oficio</option>
            </select>
            <select v-model="configPDF.orientacion" class="select select-bordered select-sm">
              <option value="portrait">Vertical</option>
              <option value="landscape">Horizontal</option>
            </select>
          </div>
        </div>

        <!-- Opciones DOCX -->
        <div v-else-if="formatoSeleccionado === 'docx'" class="space-y-2 mb-4">
          <h4 class="text-sm font-medium opacity-70">Opciones Word</h4>
          <div class="grid grid-cols-2 gap-2">
            <label class="flex items-center gap-2 cursor-pointer">
              <input v-model="configDOCX.incluir_portada" type="checkbox" class="checkbox checkbox-sm" />
              <span class="text-sm">Incluir portada</span>
            </label>
            <label class="flex items-center gap-2 cursor-pointer">
              <input v-model="configDOCX.incluir_indice" type="checkbox" class="checkbox checkbox-sm" />
              <span class="text-sm">Incluir indice</span>
            </label>
            <label class="flex items-center gap-2 cursor-pointer">
              <input v-model="configDOCX.incluir_figuras" type="checkbox" class="checkbox checkbox-sm" />
              <span class="text-sm">Incluir figuras</span>
            </label>
            <label class="flex items-center gap-2 cursor-pointer">
              <input v-model="configDOCX.incluir_tablas" type="checkbox" class="checkbox checkbox-sm" />
              <span class="text-sm">Incluir tablas</span>
            </label>
          </div>
        </div>

        <!-- Opciones e-SEIA -->
        <div v-else-if="formatoSeleccionado === 'eseia_xml'" class="space-y-2 mb-4">
          <h4 class="text-sm font-medium opacity-70">Opciones e-SEIA</h4>
          <label class="flex items-center gap-2 cursor-pointer">
            <input v-model="configESEIA.incluir_anexos_digitales" type="checkbox" class="checkbox checkbox-sm" />
            <span class="text-sm">Incluir anexos digitales</span>
          </label>
          <select v-model="configESEIA.version_esquema" class="select select-bordered select-sm w-full max-w-xs">
            <option value="2.0">Esquema e-SEIA 2.0</option>
            <option value="1.5">Esquema e-SEIA 1.5 (legacy)</option>
          </select>
        </div>

        <!-- Boton exportar -->
        <button
          class="btn btn-primary w-full"
          :disabled="exportando"
          @click="exportarDocumento"
        >
          <span v-if="exportando" class="loading loading-spinner loading-sm"></span>
          <span v-else>Exportar {{ FORMATO_EXPORTACION_LABELS[formatoSeleccionado] }}</span>
        </button>
      </div>
    </div>

    <!-- Historial de exportaciones -->
    <div class="card bg-base-100 shadow-sm">
      <div class="card-body p-4">
        <h3 class="font-bold mb-4">Exportaciones Anteriores</h3>

        <div v-if="exportacionesOrdenadas.length === 0" class="text-center py-4 opacity-60">
          <p class="text-sm">No hay exportaciones realizadas</p>
        </div>

        <div v-else class="space-y-2">
          <div
            v-for="exp in exportacionesOrdenadas"
            :key="exp.id"
            class="flex items-center justify-between p-2 bg-base-200 rounded-lg"
          >
            <div class="flex items-center gap-3">
              <div
                class="w-10 h-10 rounded flex items-center justify-center"
                :class="{
                  'bg-red-100 text-red-600': exp.formato === 'pdf',
                  'bg-blue-100 text-blue-600': exp.formato === 'docx',
                  'bg-green-100 text-green-600': exp.formato === 'eseia_xml',
                }"
              >
                <span class="text-xs font-bold uppercase">{{ exp.formato.split('_')[0] }}</span>
              </div>
              <div>
                <div class="text-sm font-medium">
                  {{ FORMATO_EXPORTACION_LABELS[exp.formato] }}
                </div>
                <div class="text-xs opacity-60">
                  {{ formatearFecha(exp.created_at) }} - {{ formatearTamano(exp.tamano_bytes) }}
                </div>
              </div>
            </div>

            <div class="flex items-center gap-2">
              <span
                v-if="exp.generado_exitoso"
                class="badge badge-success badge-sm"
              >
                OK
              </span>
              <span
                v-else
                class="badge badge-error badge-sm"
                :title="exp.error_mensaje || 'Error desconocido'"
              >
                Error
              </span>

              <button
                v-if="exp.generado_exitoso"
                class="btn btn-ghost btn-sm btn-circle"
                title="Descargar"
                @click="descargarExportacion(exp.id)"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.exportador-panel {
  max-height: 100%;
}
</style>
