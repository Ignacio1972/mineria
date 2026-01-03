<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useGeneracionEiaStore } from '@/stores/generacionEia'
import { storeToRefs } from 'pinia'
import EditorCapitulo from './EditorCapitulo.vue'
import ValidacionesPanel from './ValidacionesPanel.vue'
import VersionesHistorial from './VersionesHistorial.vue'
import ExportadorPanel from './ExportadorPanel.vue'
import {
  ESTADO_DOCUMENTO_LABELS,
  ESTADO_DOCUMENTO_COLORS,
  CAPITULOS_EIA,
} from '@/types/generacionEia'

const props = defineProps<{
  proyectoId: number
}>()

const store = useGeneracionEiaStore()
const {
  tieneDocumento,
  documento,
  estadisticas,
  capitulosGenerados,
  totalPalabras,
  porcentajeCompletitud,
  observacionesPendientes,
  observacionesError,
  esValido,
  cargando,
  compilando,
  generandoCapitulo,
  validando,
  error,
  capituloEditando,
} = storeToRefs(store)

const tabActiva = ref<'editor' | 'validaciones' | 'versiones' | 'exportar'>('editor')
const mostrarModalCompilar = ref(false)
const capitulosACompilar = ref<number[]>([])
const regenerarExistentes = ref(false)

// Computed
const capitulosDisponibles = computed(() => {
  return Object.entries(CAPITULOS_EIA).map(([num, titulo]) => ({
    numero: parseInt(num),
    titulo,
    generado: capitulosGenerados.value.includes(parseInt(num)),
  }))
})

// Cargar documento al montar o cuando cambie el proyecto
onMounted(() => {
  if (props.proyectoId) {
    store.cargarDocumentoCompleto(props.proyectoId)
  }
})

watch(() => props.proyectoId, (newId) => {
  if (newId) {
    store.cargarDocumentoCompleto(newId)
  }
})

// Acciones
async function compilarDocumento() {
  mostrarModalCompilar.value = false
  try {
    const caps = capitulosACompilar.value.length > 0 ? capitulosACompilar.value : undefined
    await store.compilarDocumento(caps, regenerarExistentes.value)
  } catch (e) {
    console.error('Error compilando documento:', e)
  }
}

async function generarCapituloIndividual(numero: number) {
  try {
    await store.generarCapitulo(numero)
  } catch (e) {
    console.error('Error generando capitulo:', e)
  }
}

async function validarDocumento() {
  try {
    await store.validarDocumento('info')
    tabActiva.value = 'validaciones'
  } catch (e) {
    console.error('Error validando documento:', e)
  }
}

function abrirModalCompilar() {
  capitulosACompilar.value = []
  regenerarExistentes.value = false
  mostrarModalCompilar.value = true
}

function seleccionarCapitulo(numero: number) {
  store.seleccionarCapitulo(numero)
}

function formatearPalabras(num: number): string {
  if (num >= 1000) {
    return `${(num / 1000).toFixed(1)}k`
  }
  return num.toString()
}
</script>

<template>
  <div class="generacion-eia h-full flex flex-col">
    <!-- Loading -->
    <div v-if="cargando" class="flex justify-center items-center py-12">
      <span class="loading loading-spinner loading-lg"></span>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="alert alert-error">
      <span>{{ error }}</span>
      <button class="btn btn-sm" @click="store.cargarDocumentoCompleto(proyectoId)">
        Reintentar
      </button>
    </div>

    <!-- Sin documento - Mostrar boton para compilar -->
    <div v-else-if="!tieneDocumento" class="flex-1 flex flex-col items-center justify-center py-12">
      <svg
        xmlns="http://www.w3.org/2000/svg"
        class="h-16 w-16 opacity-30 mb-4"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
        />
      </svg>
      <h3 class="text-lg font-semibold mb-2">Sin Documento EIA</h3>
      <p class="text-sm opacity-70 mb-4 text-center max-w-md">
        Este proyecto aun no tiene un documento EIA generado.
        Puedes compilar el documento completo o generar capitulos individuales.
      </p>
      <button
        class="btn btn-primary"
        :disabled="compilando"
        @click="abrirModalCompilar"
      >
        <span v-if="compilando" class="loading loading-spinner loading-sm"></span>
        <span v-else>Compilar Documento EIA</span>
      </button>
    </div>

    <!-- Documento existente -->
    <template v-else>
      <!-- Header con estado y estadisticas -->
      <div class="card bg-base-100 shadow-sm mb-4">
        <div class="card-body p-4">
          <div class="flex flex-wrap items-center justify-between gap-4">
            <!-- Titulo y estado -->
            <div class="flex-1 min-w-0">
              <h2 class="text-lg font-bold truncate">{{ documento?.titulo }}</h2>
              <div class="flex items-center gap-2 mt-1">
                <span
                  v-if="documento"
                  class="badge"
                  :class="ESTADO_DOCUMENTO_COLORS[documento.estado]"
                >
                  {{ ESTADO_DOCUMENTO_LABELS[documento.estado] }}
                </span>
                <span class="text-sm opacity-60">
                  Version {{ documento?.version }}
                </span>
                <span
                  v-if="esValido"
                  class="badge badge-success badge-sm gap-1"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                  </svg>
                  Valido
                </span>
                <span
                  v-else-if="observacionesError.length > 0"
                  class="badge badge-error badge-sm gap-1"
                >
                  {{ observacionesError.length }} errores
                </span>
              </div>
            </div>

            <!-- Botones principales -->
            <div class="flex gap-2">
              <button
                class="btn btn-outline btn-sm"
                :disabled="compilando"
                @click="abrirModalCompilar"
              >
                <span v-if="compilando" class="loading loading-spinner loading-xs"></span>
                <span v-else>Compilar</span>
              </button>
              <button
                class="btn btn-outline btn-sm"
                :disabled="validando"
                @click="validarDocumento"
              >
                <span v-if="validando" class="loading loading-spinner loading-xs"></span>
                <span v-else>Validar SEA</span>
              </button>
            </div>
          </div>

          <!-- Progreso general -->
          <div class="mt-4">
            <div class="flex items-center justify-between mb-1">
              <span class="text-sm font-medium">Progreso de Generacion</span>
              <span class="text-sm">{{ porcentajeCompletitud.toFixed(0) }}%</span>
            </div>
            <progress
              class="progress progress-primary w-full"
              :value="porcentajeCompletitud"
              max="100"
            ></progress>
          </div>

          <!-- Stats rapidos -->
          <div class="flex flex-wrap gap-4 mt-4 text-sm">
            <div class="flex items-center gap-1">
              <span class="font-semibold">Capitulos:</span>
              <span class="text-success">{{ capitulosGenerados.length }}</span>
              <span class="opacity-60">/</span>
              <span>11</span>
            </div>
            <div class="flex items-center gap-1">
              <span class="font-semibold">Palabras:</span>
              <span>{{ formatearPalabras(totalPalabras) }}</span>
            </div>
            <div v-if="estadisticas" class="flex items-center gap-1">
              <span class="font-semibold">Figuras:</span>
              <span>{{ estadisticas.total_figuras }}</span>
            </div>
            <div v-if="estadisticas" class="flex items-center gap-1">
              <span class="font-semibold">Tablas:</span>
              <span>{{ estadisticas.total_tablas }}</span>
            </div>
            <div class="flex items-center gap-1">
              <span class="font-semibold">Observaciones:</span>
              <span :class="observacionesPendientes.length > 0 ? 'text-warning' : 'text-success'">
                {{ observacionesPendientes.length }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Tabs -->
      <div class="tabs tabs-boxed mb-4">
        <button
          class="tab"
          :class="{ 'tab-active': tabActiva === 'editor' }"
          @click="tabActiva = 'editor'"
        >
          Editor
        </button>
        <button
          class="tab"
          :class="{ 'tab-active': tabActiva === 'validaciones' }"
          @click="tabActiva = 'validaciones'"
        >
          Validaciones
          <span
            v-if="observacionesPendientes.length > 0"
            class="badge badge-sm ml-1"
            :class="observacionesError.length > 0 ? 'badge-error' : 'badge-warning'"
          >
            {{ observacionesPendientes.length }}
          </span>
        </button>
        <button
          class="tab"
          :class="{ 'tab-active': tabActiva === 'versiones' }"
          @click="tabActiva = 'versiones'"
        >
          Versiones
        </button>
        <button
          class="tab"
          :class="{ 'tab-active': tabActiva === 'exportar' }"
          @click="tabActiva = 'exportar'"
        >
          Exportar
        </button>
      </div>

      <!-- Contenido de tabs -->
      <div class="flex-1 overflow-hidden flex">
        <!-- Tab Editor -->
        <template v-if="tabActiva === 'editor'">
          <!-- Lista de capitulos (sidebar) -->
          <div class="w-64 border-r border-base-300 overflow-y-auto pr-2">
            <div class="space-y-1">
              <button
                v-for="cap in capitulosDisponibles"
                :key="cap.numero"
                class="w-full text-left px-3 py-2 rounded-lg transition-colors text-sm"
                :class="{
                  'bg-primary text-primary-content': capituloEditando === cap.numero,
                  'hover:bg-base-200': capituloEditando !== cap.numero,
                  'opacity-50': !cap.generado && generandoCapitulo !== cap.numero,
                }"
                @click="seleccionarCapitulo(cap.numero)"
              >
                <div class="flex items-center justify-between">
                  <span class="truncate">{{ cap.numero }}. {{ cap.titulo }}</span>
                  <span v-if="generandoCapitulo === cap.numero" class="loading loading-spinner loading-xs"></span>
                  <span
                    v-else-if="cap.generado"
                    class="badge badge-success badge-xs"
                  >OK</span>
                  <button
                    v-else
                    class="btn btn-ghost btn-xs"
                    @click.stop="generarCapituloIndividual(cap.numero)"
                    title="Generar capitulo"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                    </svg>
                  </button>
                </div>
              </button>
            </div>
          </div>

          <!-- Editor de capitulo -->
          <div class="flex-1 overflow-hidden pl-4">
            <EditorCapitulo
              v-if="capituloEditando"
              :proyecto-id="proyectoId"
              :capitulo-numero="capituloEditando"
            />
            <div v-else class="flex items-center justify-center h-full text-sm opacity-60">
              Selecciona un capitulo para editar
            </div>
          </div>
        </template>

        <!-- Tab Validaciones -->
        <ValidacionesPanel
          v-else-if="tabActiva === 'validaciones'"
          :proyecto-id="proyectoId"
          class="flex-1 overflow-y-auto"
        />

        <!-- Tab Versiones -->
        <VersionesHistorial
          v-else-if="tabActiva === 'versiones'"
          :proyecto-id="proyectoId"
          class="flex-1 overflow-y-auto"
        />

        <!-- Tab Exportar -->
        <ExportadorPanel
          v-else-if="tabActiva === 'exportar'"
          :proyecto-id="proyectoId"
          class="flex-1 overflow-y-auto"
        />
      </div>
    </template>

    <!-- Modal Compilar -->
    <dialog
      class="modal"
      :class="{ 'modal-open': mostrarModalCompilar }"
    >
      <div class="modal-box">
        <h3 class="font-bold text-lg mb-4">Compilar Documento EIA</h3>

        <div class="form-control mb-4">
          <label class="label cursor-pointer justify-start gap-2">
            <input
              v-model="regenerarExistentes"
              type="checkbox"
              class="checkbox checkbox-primary checkbox-sm"
            />
            <span class="label-text">Regenerar capitulos existentes</span>
          </label>
        </div>

        <div class="mb-4">
          <label class="label">
            <span class="label-text">Capitulos a generar (vacio = todos)</span>
          </label>
          <div class="flex flex-wrap gap-2">
            <label
              v-for="cap in capitulosDisponibles"
              :key="cap.numero"
              class="flex items-center gap-1 cursor-pointer"
            >
              <input
                v-model="capitulosACompilar"
                type="checkbox"
                :value="cap.numero"
                class="checkbox checkbox-xs"
              />
              <span class="text-xs">{{ cap.numero }}</span>
            </label>
          </div>
        </div>

        <div class="alert alert-info text-sm mb-4">
          <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-5 w-5" fill="none" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>La compilacion puede tomar varios minutos dependiendo de la cantidad de capitulos.</span>
        </div>

        <div class="modal-action">
          <button class="btn btn-ghost" @click="mostrarModalCompilar = false">
            Cancelar
          </button>
          <button
            class="btn btn-primary"
            :disabled="compilando"
            @click="compilarDocumento"
          >
            <span v-if="compilando" class="loading loading-spinner loading-sm"></span>
            <span v-else>Compilar</span>
          </button>
        </div>
      </div>
      <form method="dialog" class="modal-backdrop">
        <button @click="mostrarModalCompilar = false">close</button>
      </form>
    </dialog>
  </div>
</template>

<style scoped>
.generacion-eia {
  max-height: calc(100vh - 200px);
}
</style>
