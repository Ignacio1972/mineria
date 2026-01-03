<script setup lang="ts">
import { ref, computed } from 'vue'
import { useGeneracionEiaStore } from '@/stores/generacionEia'
import { storeToRefs } from 'pinia'
import {
  SEVERIDAD_LABELS,
  SEVERIDAD_COLORS,
  CAPITULOS_EIA,
  type SeveridadValidacion,
} from '@/types/generacionEia'

const props = defineProps<{
  proyectoId: number
}>()

const store = useGeneracionEiaStore()
const {
  observacionesPendientes,
  observacionesError,
  observacionesWarning,
  esValido,
  validando,
} = storeToRefs(store)

const filtroSeveridad = ref<SeveridadValidacion | 'todas'>('todas')
const filtroCapitulo = ref<number | null>(null)

// Observaciones filtradas
const observacionesFiltradas = computed(() => {
  let resultado = observacionesPendientes.value

  if (filtroSeveridad.value !== 'todas') {
    resultado = resultado.filter(o => o.severidad === filtroSeveridad.value)
  }

  if (filtroCapitulo.value !== null) {
    resultado = resultado.filter(o => o.capitulo_numero === filtroCapitulo.value)
  }

  return resultado
})

// Capitulos con observaciones
const capitulosConObservaciones = computed(() => {
  const caps = new Set<number>()
  observacionesPendientes.value.forEach(o => {
    if (o.capitulo_numero) caps.add(o.capitulo_numero)
  })
  return Array.from(caps).sort((a, b) => a - b)
})

// Resumen por severidad
const resumenSeveridad = computed(() => ({
  error: observacionesError.value.length,
  warning: observacionesWarning.value.length,
  info: observacionesPendientes.value.filter(o => o.severidad === 'info').length,
}))

// Acciones
async function validarDocumento() {
  try {
    await store.validarDocumento('info')
  } catch (e) {
    console.error('Error validando:', e)
  }
}

function getTituloCapitulo(numero: number | null | undefined): string {
  if (!numero) return 'General'
  return CAPITULOS_EIA[numero] || `Capitulo ${numero}`
}
</script>

<template>
  <div class="validaciones-panel p-4">
    <!-- Resumen -->
    <div class="card bg-base-100 shadow-sm mb-4">
      <div class="card-body p-4">
        <div class="flex items-center justify-between">
          <div>
            <h3 class="font-bold text-lg">Validacion SEA</h3>
            <p class="text-sm opacity-60">
              Verifica el documento contra reglas del SEA e ICSARA
            </p>
          </div>
          <button
            class="btn btn-primary btn-sm"
            :disabled="validando"
            @click="validarDocumento"
          >
            <span v-if="validando" class="loading loading-spinner loading-xs"></span>
            <span v-else>Validar Ahora</span>
          </button>
        </div>

        <!-- Estado general -->
        <div class="mt-4">
          <div
            v-if="esValido"
            class="alert alert-success"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>El documento cumple con los requisitos basicos del SEA</span>
          </div>
          <div
            v-else-if="observacionesError.length > 0"
            class="alert alert-error"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>Hay {{ observacionesError.length }} errores que deben corregirse</span>
          </div>
          <div
            v-else-if="observacionesPendientes.length > 0"
            class="alert alert-warning"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <span>Hay {{ observacionesPendientes.length }} observaciones pendientes</span>
          </div>
        </div>

        <!-- Contadores por severidad -->
        <div class="flex gap-4 mt-4">
          <div class="stat p-2">
            <div class="stat-title text-xs">Errores</div>
            <div class="stat-value text-error text-2xl">{{ resumenSeveridad.error }}</div>
          </div>
          <div class="stat p-2">
            <div class="stat-title text-xs">Advertencias</div>
            <div class="stat-value text-warning text-2xl">{{ resumenSeveridad.warning }}</div>
          </div>
          <div class="stat p-2">
            <div class="stat-title text-xs">Info</div>
            <div class="stat-value text-info text-2xl">{{ resumenSeveridad.info }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Filtros -->
    <div class="flex gap-2 mb-4">
      <select
        v-model="filtroSeveridad"
        class="select select-bordered select-sm"
      >
        <option value="todas">Todas las severidades</option>
        <option value="error">Solo errores</option>
        <option value="warning">Solo advertencias</option>
        <option value="info">Solo info</option>
      </select>

      <select
        v-model="filtroCapitulo"
        class="select select-bordered select-sm"
      >
        <option :value="null">Todos los capitulos</option>
        <option
          v-for="cap in capitulosConObservaciones"
          :key="cap"
          :value="cap"
        >
          {{ cap }}. {{ CAPITULOS_EIA[cap] }}
        </option>
      </select>
    </div>

    <!-- Lista de observaciones -->
    <div v-if="observacionesFiltradas.length === 0" class="text-center py-8 opacity-60">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <p>No hay observaciones con los filtros seleccionados</p>
    </div>

    <div v-else class="space-y-2">
      <div
        v-for="obs in observacionesFiltradas"
        :key="obs.id"
        class="card bg-base-100 shadow-sm"
      >
        <div class="card-body p-3">
          <div class="flex items-start gap-3">
            <!-- Icono severidad -->
            <div
              class="w-8 h-8 rounded-full flex items-center justify-center shrink-0"
              :class="{
                'bg-error/20 text-error': obs.severidad === 'error',
                'bg-warning/20 text-warning': obs.severidad === 'warning',
                'bg-info/20 text-info': obs.severidad === 'info',
              }"
            >
              <svg
                v-if="obs.severidad === 'error'"
                xmlns="http://www.w3.org/2000/svg"
                class="h-5 w-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
              <svg
                v-else-if="obs.severidad === 'warning'"
                xmlns="http://www.w3.org/2000/svg"
                class="h-5 w-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <svg
                v-else
                xmlns="http://www.w3.org/2000/svg"
                class="h-5 w-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>

            <!-- Contenido -->
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-1">
                <span class="badge badge-sm" :class="SEVERIDAD_COLORS[obs.severidad]">
                  {{ SEVERIDAD_LABELS[obs.severidad] }}
                </span>
                <span class="text-xs opacity-60">
                  {{ getTituloCapitulo(obs.capitulo_numero) }}
                  <span v-if="obs.seccion"> - {{ obs.seccion }}</span>
                </span>
              </div>
              <p class="text-sm font-medium">{{ obs.mensaje }}</p>
              <p v-if="obs.sugerencia" class="text-sm opacity-70 mt-1">
                <strong>Sugerencia:</strong> {{ obs.sugerencia }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.validaciones-panel {
  max-height: 100%;
}
</style>
