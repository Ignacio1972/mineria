<script setup lang="ts">
import { computed } from 'vue'
import { useGeneracionEiaStore } from '@/stores/generacionEia'
import { storeToRefs } from 'pinia'
import {
  ESTADO_GENERACION_LABELS,
  ESTADO_GENERACION_COLORS,
  CAPITULOS_EIA,
} from '@/types/generacionEia'

const props = defineProps<{
  proyectoId: number
}>()

const store = useGeneracionEiaStore()
const {
  progreso,
  estadisticas,
  porcentajeCompletitud,
  generandoCapitulo,
} = storeToRefs(store)

// Progreso por capitulo ordenado
const progresoOrdenado = computed(() => {
  return [...progreso.value].sort((a, b) => a.capitulo_numero - b.capitulo_numero)
})

// Estadisticas calculadas
const capitulosCompletados = computed(() =>
  progreso.value.filter(p => p.estado === 'completado').length
)

const totalPalabras = computed(() =>
  progreso.value.reduce((sum, p) => sum + p.palabras_generadas, 0)
)

function formatearPalabras(num: number): string {
  if (num >= 1000) {
    return `${(num / 1000).toFixed(1)}k`
  }
  return num.toString()
}

function getTituloCapitulo(numero: number): string {
  return CAPITULOS_EIA[numero] || `Capitulo ${numero}`
}
</script>

<template>
  <div class="progreso-generacion p-4">
    <!-- Resumen general -->
    <div class="card bg-base-100 shadow-sm mb-4">
      <div class="card-body p-4">
        <h3 class="font-bold text-lg mb-4">Progreso de Generacion</h3>

        <!-- Barra de progreso general -->
        <div class="mb-4">
          <div class="flex items-center justify-between mb-1">
            <span class="text-sm font-medium">Completitud General</span>
            <span class="text-sm">{{ porcentajeCompletitud.toFixed(0) }}%</span>
          </div>
          <progress
            class="progress progress-primary w-full h-4"
            :value="porcentajeCompletitud"
            max="100"
          ></progress>
        </div>

        <!-- Estadisticas -->
        <div class="grid grid-cols-3 gap-4">
          <div class="stat bg-base-200 rounded-lg p-3">
            <div class="stat-title text-xs">Capitulos</div>
            <div class="stat-value text-xl">{{ capitulosCompletados }}/11</div>
          </div>
          <div class="stat bg-base-200 rounded-lg p-3">
            <div class="stat-title text-xs">Palabras</div>
            <div class="stat-value text-xl">{{ formatearPalabras(totalPalabras) }}</div>
          </div>
          <div v-if="estadisticas" class="stat bg-base-200 rounded-lg p-3">
            <div class="stat-title text-xs">Figuras</div>
            <div class="stat-value text-xl">{{ estadisticas.total_figuras }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Progreso por capitulo -->
    <div class="card bg-base-100 shadow-sm">
      <div class="card-body p-4">
        <h4 class="font-bold mb-4">Detalle por Capitulo</h4>

        <div class="space-y-3">
          <div
            v-for="cap in progresoOrdenado"
            :key="cap.capitulo_numero"
            class="flex items-center gap-3 p-2 bg-base-200 rounded-lg"
          >
            <!-- Numero -->
            <div
              class="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold shrink-0"
              :class="{
                'bg-success text-success-content': cap.estado === 'completado',
                'bg-warning text-warning-content': cap.estado === 'generando',
                'bg-error text-error-content': cap.estado === 'error',
                'bg-base-300': cap.estado === 'pendiente',
              }"
            >
              {{ cap.capitulo_numero }}
            </div>

            <!-- Info -->
            <div class="flex-1 min-w-0">
              <div class="flex items-center justify-between">
                <span class="text-sm font-medium truncate">{{ getTituloCapitulo(cap.capitulo_numero) }}</span>
                <span
                  class="badge badge-sm ml-2"
                  :class="ESTADO_GENERACION_COLORS[cap.estado]"
                >
                  {{ ESTADO_GENERACION_LABELS[cap.estado] }}
                </span>
              </div>

              <!-- Barra de progreso individual -->
              <div class="flex items-center gap-2 mt-1">
                <progress
                  class="progress progress-sm flex-1"
                  :class="{
                    'progress-success': cap.estado === 'completado',
                    'progress-warning': cap.estado === 'generando',
                    'progress-error': cap.estado === 'error',
                  }"
                  :value="cap.progreso_porcentaje"
                  max="100"
                ></progress>
                <span class="text-xs opacity-60 w-12 text-right">
                  {{ cap.palabras_generadas > 0 ? formatearPalabras(cap.palabras_generadas) + ' pal.' : '-' }}
                </span>
              </div>

              <!-- Error si existe -->
              <div v-if="cap.error" class="text-xs text-error mt-1">
                {{ cap.error }}
              </div>
            </div>

            <!-- Indicador de generando -->
            <span
              v-if="generandoCapitulo === cap.capitulo_numero"
              class="loading loading-spinner loading-sm"
            ></span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.progreso-generacion {
  max-height: 100%;
}
</style>
