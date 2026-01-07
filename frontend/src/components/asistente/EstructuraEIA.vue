<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useEstructuraEiaStore } from '@/stores/estructuraEia'
import { storeToRefs } from 'pinia'
import CapitulosList from './estructura/CapitulosList.vue'
import PASList from './estructura/PASList.vue'
import AnexosList from './estructura/AnexosList.vue'
import LineaBaseList from './estructura/LineaBaseList.vue'
import {
  NIVEL_COMPLEJIDAD_LABELS,
  NIVEL_COMPLEJIDAD_COLORS,
  type EstadoCapitulo,
  type EstadoPAS,
  type EstadoAnexo,
} from '@/types'

const props = defineProps<{
  proyectoId: number
}>()

const store = useEstructuraEiaStore()
const {
  tieneEstructura,
  estructura,
  capitulos,
  pasRequeridos,
  anexos,
  planLineaBase,
  estimacion,
  progresoGeneral,
  capitulosCompletados,
  pasAprobados,
  nivelComplejidad,
  tiempoEstimadoMeses,
  cargando,
  generando,
  error,
} = storeToRefs(store)

const tabActiva = ref<'capitulos' | 'pas' | 'anexos' | 'linea-base'>('capitulos')

// Cargar estructura al montar o cuando cambie el proyecto
onMounted(() => {
  if (props.proyectoId) {
    store.cargarEstructura(props.proyectoId)
  }
})

watch(() => props.proyectoId, (newId) => {
  if (newId) {
    store.cargarEstructura(newId)
  }
})

// Acciones
async function generarEstructura(forzar: boolean = false) {
  try {
    await store.generarEstructura(props.proyectoId, forzar)
  } catch (e) {
    console.error('Error generando estructura:', e)
  }
}

async function actualizarCapitulo(numero: number, estado: EstadoCapitulo) {
  try {
    await store.actualizarCapitulo(numero, { estado })
  } catch (e) {
    console.error('Error actualizando capitulo:', e)
  }
}

async function actualizarPAS(articulo: number, estado: EstadoPAS) {
  try {
    await store.actualizarPAS(articulo, { estado })
  } catch (e) {
    console.error('Error actualizando PAS:', e)
  }
}

async function actualizarAnexo(codigo: string, estado: EstadoAnexo) {
  try {
    await store.actualizarAnexo(codigo, { estado })
  } catch (e) {
    console.error('Error actualizando anexo:', e)
  }
}

function verDetalleCapitulo(numero: number) {
  // TODO: Abrir modal con detalle del capitulo
  console.log('Ver detalle capitulo:', numero)
}
</script>

<template>
  <div class="estructura-eia h-full flex flex-col">
    <!-- Loading -->
    <div v-if="cargando" class="flex justify-center items-center py-12">
      <span class="loading loading-spinner loading-lg"></span>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="alert alert-error">
      <span>{{ error }}</span>
      <button class="btn btn-sm" @click="store.cargarEstructura(proyectoId)">
        Reintentar
      </button>
    </div>

    <!-- Sin estructura - Mostrar boton para generar -->
    <div v-else-if="!tieneEstructura" class="flex-1 flex flex-col items-center justify-center py-12">
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
      <h3 class="text-lg font-semibold mb-2">Sin Estructura EIA</h3>
      <p class="text-sm opacity-70 mb-4 text-center max-w-md">
        Este proyecto aun no tiene estructura EIA generada.
        La estructura incluye los 11 capitulos del EIA, PAS requeridos,
        anexos tecnicos y plan de linea base.
      </p>
      <button
        class="btn btn-primary"
        :disabled="generando"
        @click="generarEstructura(false)"
      >
        <span v-if="generando" class="loading loading-spinner loading-sm"></span>
        <span v-else>Generar Estructura EIA</span>
      </button>
    </div>

    <!-- Estructura existente -->
    <template v-else>
      <!-- Header con resumen y complejidad -->
      <div class="card bg-base-100 shadow-sm mb-4">
        <div class="card-body p-4">
          <div class="flex flex-wrap items-center justify-between gap-4">
            <!-- Titulo y version -->
            <div>
              <h2 class="text-lg font-bold">Estructura del EIA</h2>
              <p class="text-sm opacity-60">
                Version {{ estructura?.version }} -
                Creada {{ new Date(estructura?.created_at || '').toLocaleDateString() }}
              </p>
            </div>

            <!-- Badge complejidad -->
            <div v-if="nivelComplejidad" class="flex items-center gap-3">
              <div class="text-right">
                <div class="text-xs opacity-60">Complejidad</div>
                <span
                  class="badge badge-lg"
                  :class="NIVEL_COMPLEJIDAD_COLORS[nivelComplejidad]"
                >
                  {{ NIVEL_COMPLEJIDAD_LABELS[nivelComplejidad] }}
                </span>
              </div>
              <div v-if="tiempoEstimadoMeses" class="text-center">
                <div class="text-2xl font-bold">{{ tiempoEstimadoMeses }}</div>
                <div class="text-xs opacity-60">meses est.</div>
              </div>
            </div>
          </div>

          <!-- Progreso general -->
          <div class="mt-4">
            <div class="flex items-center justify-between mb-1">
              <span class="text-sm font-medium">Progreso General</span>
              <span class="text-sm">{{ progresoGeneral }}%</span>
            </div>
            <progress
              class="progress progress-primary w-full"
              :value="progresoGeneral"
              max="100"
            ></progress>
          </div>

          <!-- Stats rapidos -->
          <div class="flex flex-wrap gap-4 mt-4 text-sm">
            <div class="flex items-center gap-1">
              <span class="font-semibold">Capitulos:</span>
              <span class="text-success">{{ capitulosCompletados }}</span>
              <span class="opacity-60">/</span>
              <span>{{ capitulos.length }}</span>
            </div>
            <div class="flex items-center gap-1">
              <span class="font-semibold">PAS:</span>
              <span class="text-success">{{ pasAprobados }}</span>
              <span class="opacity-60">/</span>
              <span>{{ pasRequeridos.length }}</span>
            </div>
            <div class="flex items-center gap-1">
              <span class="font-semibold">Anexos:</span>
              <span>{{ anexos.length }}</span>
            </div>
            <div class="flex items-center gap-1">
              <span class="font-semibold">Linea Base:</span>
              <span>{{ planLineaBase.length }} componentes</span>
            </div>
          </div>

          <!-- Boton regenerar -->
          <div class="mt-4">
            <button
              class="btn btn-outline btn-sm"
              :disabled="generando"
              @click="generarEstructura(true)"
            >
              <span v-if="generando" class="loading loading-spinner loading-xs"></span>
              <span v-else>Regenerar Estructura</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Riesgos y recomendaciones -->
      <div v-if="estimacion" class="mb-4">
        <details class="collapse collapse-arrow bg-base-200">
          <summary class="collapse-title text-sm font-medium py-3">
            Riesgos y Recomendaciones
          </summary>
          <div class="collapse-content">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
              <!-- Riesgos -->
              <div v-if="estimacion.riesgos_principales?.length">
                <h4 class="font-semibold text-sm mb-2 text-warning">Riesgos Principales</h4>
                <ul class="list-disc list-inside text-sm opacity-80 space-y-1">
                  <li v-for="(riesgo, idx) in estimacion.riesgos_principales" :key="idx">
                    {{ riesgo }}
                  </li>
                </ul>
              </div>

              <!-- Recomendaciones -->
              <div v-if="estimacion.recomendaciones?.length">
                <h4 class="font-semibold text-sm mb-2 text-info">Recomendaciones</h4>
                <ul class="list-disc list-inside text-sm opacity-80 space-y-1">
                  <li v-for="(rec, idx) in estimacion.recomendaciones" :key="idx">
                    {{ rec }}
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </details>
      </div>

      <!-- Tabs -->
      <div class="tabs tabs-boxed mb-4">
        <button
          class="tab"
          :class="{ 'tab-active': tabActiva === 'capitulos' }"
          @click="tabActiva = 'capitulos'"
        >
          Capitulos ({{ capitulos.length }})
        </button>
        <button
          class="tab"
          :class="{ 'tab-active': tabActiva === 'pas' }"
          @click="tabActiva = 'pas'"
        >
          PAS ({{ pasRequeridos.length }})
        </button>
        <button
          class="tab"
          :class="{ 'tab-active': tabActiva === 'anexos' }"
          @click="tabActiva = 'anexos'"
        >
          Anexos ({{ anexos.length }})
        </button>
        <button
          class="tab"
          :class="{ 'tab-active': tabActiva === 'linea-base' }"
          @click="tabActiva = 'linea-base'"
        >
          Linea Base
        </button>
      </div>

      <!-- Contenido de tabs -->
      <div class="overflow-y-auto border border-base-300 rounded-lg p-4" style="height: 600px;">
        <CapitulosList
          v-if="tabActiva === 'capitulos'"
          :capitulos="capitulos"
          @actualizar="actualizarCapitulo"
          @ver-detalle="verDetalleCapitulo"
        />

        <PASList
          v-else-if="tabActiva === 'pas'"
          :pas="pasRequeridos"
          @actualizar="actualizarPAS"
        />

        <AnexosList
          v-else-if="tabActiva === 'anexos'"
          :anexos="anexos"
          @actualizar="actualizarAnexo"
        />

        <LineaBaseList
          v-else-if="tabActiva === 'linea-base'"
          :componentes="planLineaBase"
        />
      </div>

    </template>
  </div>
</template>

<style scoped>
.estructura-eia {
  min-height: 500px;
}
</style>
