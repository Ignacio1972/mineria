<script setup lang="ts">
/**
 * Componente para mostrar documentos requeridos según SEA.
 * Muestra el checklist de documentación con estado de cumplimiento.
 */
import { ref, computed, onMounted, watch } from 'vue'
import { get } from '@/services/api'
import type {
  DocumentosRequeridosResponse,
  DocumentoRequeridoEstado,
  ValidacionCompletitudResponse,
  SeccionEIA,
  CategoriaDocumentoSEA,
  DocumentosPorSeccion,
} from '@/types/documento'
import {
  SECCIONES_EIA,
  ESTADO_VALIDACION_CONFIG,
  getDocumentosPorSeccion,
} from '@/types/documento'

// Props
const props = defineProps<{
  proyectoId: number
  readonly?: boolean
}>()

// Emits
const emit = defineEmits<{
  (e: 'subir-documento', categoria: CategoriaDocumentoSEA): void
  (e: 'ver-documento', documentoId: string): void
  (e: 'completitud-cambiada', completitud: ValidacionCompletitudResponse): void
}>()

// State
const loading = ref(false)
const error = ref<string | null>(null)
const documentosRequeridos = ref<DocumentosRequeridosResponse | null>(null)
const completitud = ref<ValidacionCompletitudResponse | null>(null)
const seccionExpandida = ref<SeccionEIA | null>('descripcion_proyecto')
const mostrarSoloObligatorios = ref(false)
const mostrarSoloFaltantes = ref(false)

// Computed
const documentosPorSeccion = computed<DocumentosPorSeccion>(() => {
  if (!documentosRequeridos.value) return {} as DocumentosPorSeccion

  let items = documentosRequeridos.value.items

  // Filtrar por obligatorios
  if (mostrarSoloObligatorios.value) {
    items = items.filter((d) => d.obligatorio_segun_via)
  }

  // Filtrar por faltantes
  if (mostrarSoloFaltantes.value) {
    items = items.filter((d) => d.estado_cumplimiento === 'pendiente')
  }

  return getDocumentosPorSeccion(items)
})

const seccionesConDocumentos = computed(() => {
  return SECCIONES_EIA.filter((s) => {
    const docs = documentosPorSeccion.value[s.value]
    return docs && docs.length > 0
  })
})

const porcentajeCompletitud = computed(() => {
  return completitud.value?.porcentaje_completitud || 0
})

const colorProgreso = computed(() => {
  const pct = porcentajeCompletitud.value
  if (pct >= 80) return 'progress-success'
  if (pct >= 50) return 'progress-warning'
  return 'progress-error'
})

// Methods
async function cargarDatos() {
  loading.value = true
  error.value = null

  try {
    const [requeridosRes, completitudRes] = await Promise.all([
      get<DocumentosRequeridosResponse>(`/documentos/proyectos/${props.proyectoId}/requeridos`),
      get<ValidacionCompletitudResponse>(`/documentos/proyectos/${props.proyectoId}/validar-completitud`),
    ])

    documentosRequeridos.value = requeridosRes
    completitud.value = completitudRes

    emit('completitud-cambiada', completitudRes)
  } catch (err: unknown) {
    const apiError = err as { detail?: string }
    error.value = apiError.detail || 'Error cargando documentos requeridos'
  } finally {
    loading.value = false
  }
}

function toggleSeccion(seccion: SeccionEIA) {
  if (seccionExpandida.value === seccion) {
    seccionExpandida.value = null
  } else {
    seccionExpandida.value = seccion
  }
}

function getEstadoConfig(estado: string) {
  return ESTADO_VALIDACION_CONFIG[estado as keyof typeof ESTADO_VALIDACION_CONFIG] || ESTADO_VALIDACION_CONFIG.pendiente
}

function contarDocumentosSeccion(seccion: SeccionEIA) {
  const docs = documentosPorSeccion.value[seccion] || []
  const total = docs.length
  const completados = docs.filter((d) => d.estado_cumplimiento !== 'pendiente').length
  return { total, completados }
}

function handleSubirDocumento(doc: DocumentoRequeridoEstado) {
  emit('subir-documento', doc.categoria_sea)
}

function handleVerDocumento(doc: DocumentoRequeridoEstado) {
  if (doc.documento_id) {
    emit('ver-documento', doc.documento_id)
  }
}

// Lifecycle
onMounted(() => {
  cargarDatos()
})

watch(
  () => props.proyectoId,
  () => {
    cargarDatos()
  }
)

// Expose para refrescar desde padre
defineExpose({
  refrescar: cargarDatos,
})
</script>

<template>
  <div class="documentos-requeridos">
    <!-- Header con resumen -->
    <div class="card bg-base-100 shadow-sm mb-4">
      <div class="card-body p-4">
        <div class="flex items-center justify-between mb-3">
          <h3 class="card-title text-lg">Documentación Requerida SEA</h3>
          <div v-if="documentosRequeridos" class="badge badge-outline">
            {{ documentosRequeridos.via_evaluacion }}
          </div>
        </div>

        <!-- Barra de progreso -->
        <div v-if="completitud" class="mb-4">
          <div class="flex justify-between text-sm mb-1">
            <span>Completitud</span>
            <span class="font-medium">{{ porcentajeCompletitud }}%</span>
          </div>
          <progress
            class="progress w-full"
            :class="colorProgreso"
            :value="porcentajeCompletitud"
            max="100"
          ></progress>
          <div class="flex justify-between text-xs text-base-content/60 mt-1">
            <span>{{ completitud.total_subidos }} de {{ completitud.total_requeridos }} documentos</span>
            <span v-if="completitud.total_obligatorios > 0">
              {{ completitud.total_obligatorios - completitud.obligatorios_faltantes.length }}/{{ completitud.total_obligatorios }} obligatorios
            </span>
          </div>
        </div>

        <!-- Alertas -->
        <div v-if="completitud?.alertas.length" class="space-y-2">
          <div
            v-for="(alerta, idx) in completitud.alertas"
            :key="idx"
            class="alert alert-warning py-2"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-5 w-5" fill="none" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <span class="text-sm">{{ alerta }}</span>
          </div>
        </div>

        <!-- Filtros -->
        <div class="flex gap-4 mt-3">
          <label class="label cursor-pointer gap-2">
            <input
              type="checkbox"
              v-model="mostrarSoloObligatorios"
              class="checkbox checkbox-sm checkbox-primary"
            />
            <span class="label-text text-sm">Solo obligatorios</span>
          </label>
          <label class="label cursor-pointer gap-2">
            <input
              type="checkbox"
              v-model="mostrarSoloFaltantes"
              class="checkbox checkbox-sm checkbox-warning"
            />
            <span class="label-text text-sm">Solo faltantes</span>
          </label>
        </div>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-8">
      <span class="loading loading-spinner loading-lg"></span>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="alert alert-error">
      <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <span>{{ error }}</span>
      <button class="btn btn-sm" @click="cargarDatos">Reintentar</button>
    </div>

    <!-- Lista de secciones -->
    <div v-else class="space-y-2">
      <div
        v-for="seccion in seccionesConDocumentos"
        :key="seccion.value"
        class="collapse collapse-arrow bg-base-100 shadow-sm"
        :class="{ 'collapse-open': seccionExpandida === seccion.value }"
      >
        <input
          type="radio"
          name="seccion-accordion"
          :checked="seccionExpandida === seccion.value"
          @click="toggleSeccion(seccion.value)"
        />
        <div class="collapse-title font-medium flex items-center justify-between pr-12">
          <span>{{ seccion.label }}</span>
          <div class="flex items-center gap-2">
            <span class="text-sm text-base-content/60">
              {{ contarDocumentosSeccion(seccion.value).completados }}/{{ contarDocumentosSeccion(seccion.value).total }}
            </span>
            <div
              v-if="contarDocumentosSeccion(seccion.value).completados === contarDocumentosSeccion(seccion.value).total"
              class="badge badge-success badge-sm"
            >
              Completo
            </div>
          </div>
        </div>
        <div class="collapse-content">
          <div class="overflow-x-auto">
            <table class="table table-sm">
              <thead>
                <tr>
                  <th>Documento</th>
                  <th class="w-24 text-center">Estado</th>
                  <th class="w-32 text-center">Acciones</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="doc in documentosPorSeccion[seccion.value]"
                  :key="doc.requerimiento_id"
                  class="hover"
                >
                  <td>
                    <div class="flex items-start gap-2">
                      <div>
                        <div class="font-medium flex items-center gap-2">
                          {{ doc.nombre_display }}
                          <span
                            v-if="doc.obligatorio_segun_via"
                            class="badge badge-error badge-xs"
                          >
                            Obligatorio
                          </span>
                        </div>
                        <div v-if="doc.descripcion" class="text-xs text-base-content/60">
                          {{ doc.descripcion }}
                        </div>
                        <div v-if="doc.notas_sea" class="text-xs text-info mt-1">
                          SEA: {{ doc.notas_sea }}
                        </div>
                        <div v-if="doc.documento_nombre" class="text-xs text-success mt-1">
                          Archivo: {{ doc.documento_nombre }}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td class="text-center">
                    <div
                      class="badge"
                      :class="`badge-${getEstadoConfig(doc.estado_cumplimiento).color}`"
                    >
                      {{ getEstadoConfig(doc.estado_cumplimiento).label }}
                    </div>
                  </td>
                  <td class="text-center">
                    <div class="flex justify-center gap-1">
                      <button
                        v-if="doc.estado_cumplimiento === 'pendiente' && !readonly"
                        class="btn btn-xs btn-primary"
                        @click="handleSubirDocumento(doc)"
                      >
                        Subir
                      </button>
                      <button
                        v-if="doc.documento_id"
                        class="btn btn-xs btn-ghost"
                        @click="handleVerDocumento(doc)"
                      >
                        Ver
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- Estado cuando todo está completo -->
    <div
      v-if="completitud?.es_completo && !loading"
      class="alert alert-success mt-4"
    >
      <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <span>Documentación obligatoria completa. El proyecto puede continuar al análisis.</span>
    </div>
  </div>
</template>

<style scoped>
.documentos-requeridos {
  @apply w-full;
}

.collapse-title {
  @apply min-h-0 py-3;
}

.collapse-content {
  @apply pb-4;
}
</style>
