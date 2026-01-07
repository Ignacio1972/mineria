<script setup lang="ts">
/**
 * ProgresoIntegral.vue
 * Dashboard visual del progreso del proyecto a través de las 5 fases del workflow EIA.
 */
import { computed, onMounted, watch } from 'vue'
import { useComponentesStore } from '@/stores'
import type { FaseProyecto } from '@/types'

const props = defineProps<{
  proyectoId: number
}>()

const emit = defineEmits<{
  (e: 'irAFase', fase: FaseProyecto): void
}>()

const componentesStore = useComponentesStore()

// Cargar datos al montar y cuando cambie el proyecto
onMounted(() => {
  componentesStore.cargarTodo(props.proyectoId)
})

watch(
  () => props.proyectoId,
  (newId) => {
    componentesStore.cargarTodo(newId)
  }
)

// Iconos para cada fase
const iconosFases: Record<FaseProyecto, string> = {
  identificacion: 'M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z M15 11a3 3 0 11-6 0 3 3 0 016 0z',
  prefactibilidad: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4',
  recopilacion: 'M5 19a2 2 0 01-2-2V7a2 2 0 012-2h4l2 2h4a2 2 0 012 2v1M5 19h14a2 2 0 002-2v-5a2 2 0 00-2-2H9a2 2 0 00-2 2v5a2 2 0 01-2 2z',
  generacion: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
  refinamiento: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
}

// Colores para cada fase
const coloresFases: Record<FaseProyecto, string> = {
  identificacion: 'text-primary',
  prefactibilidad: 'text-secondary',
  recopilacion: 'text-accent',
  generacion: 'text-info',
  refinamiento: 'text-success',
}

// Color de fondo para fase activa
const bgFaseActiva: Record<FaseProyecto, string> = {
  identificacion: 'bg-primary/10 border-primary',
  prefactibilidad: 'bg-secondary/10 border-secondary',
  recopilacion: 'bg-accent/10 border-accent',
  generacion: 'bg-info/10 border-info',
  refinamiento: 'bg-success/10 border-success',
}

// Acciones contextuales por fase
const accionesFases: Record<FaseProyecto, string | null> = {
  identificacion: 'Dibujar geometria',
  prefactibilidad: 'Ejecutar analisis',
  recopilacion: 'Ver checklist',
  generacion: 'Generar EIA',
  refinamiento: 'Validar documento',
}

// Progreso visual de la fase
const progresoFase = computed(() => (rango: [number, number]) => {
  const progreso = componentesStore.progresoGlobal
  const [min, max] = rango
  if (progreso < min) return 0
  if (progreso >= max) return 100
  return Math.round(((progreso - min) / (max - min)) * 100)
})
</script>

<template>
  <div class="card bg-gradient-to-br from-base-100 to-base-200 shadow-lg border border-base-300">
    <div class="card-body">
      <!-- Header -->
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-4">
        <div>
          <h3 class="font-bold text-lg">Progreso del Workflow EIA</h3>
          <p class="text-sm text-base-content/60">
            Fase actual:
            <span class="font-semibold capitalize">{{ componentesStore.faseActual }}</span>
          </p>
        </div>
        <div class="flex items-center gap-3">
          <div
            class="radial-progress text-primary"
            :style="`--value:${componentesStore.progresoGlobal}; --size:3.5rem; --thickness:4px;`"
            role="progressbar"
          >
            <span class="text-sm font-bold">{{ componentesStore.progresoGlobal }}%</span>
          </div>
        </div>
      </div>

      <!-- Barra de progreso global -->
      <progress
        class="progress progress-primary w-full h-3 mb-6"
        :value="componentesStore.progresoGlobal"
        max="100"
      ></progress>

      <!-- Grid de 5 fases -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <div
          v-for="fase in componentesStore.progreso?.fases || []"
          :key="fase.id"
          class="relative p-4 rounded-lg border-2 transition-all cursor-pointer hover:shadow-md"
          :class="[
            fase.activa ? bgFaseActiva[fase.id as FaseProyecto] : 'bg-base-100 border-base-300',
            fase.completada ? 'opacity-100' : 'opacity-80',
          ]"
          @click="emit('irAFase', fase.id as FaseProyecto)"
        >
          <!-- Indicador de completado -->
          <div
            v-if="fase.completada"
            class="absolute -top-2 -right-2 w-6 h-6 bg-success text-success-content rounded-full flex items-center justify-center"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
          </div>

          <!-- Icono y titulo -->
          <div class="flex items-center gap-2 mb-2">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-6 w-6"
              :class="coloresFases[fase.id as FaseProyecto]"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                :d="iconosFases[fase.id as FaseProyecto]"
              />
            </svg>
            <span class="font-semibold text-sm">{{ fase.nombre }}</span>
          </div>

          <!-- Descripcion -->
          <p class="text-xs text-base-content/60 mb-3 line-clamp-2">
            {{ fase.descripcion }}
          </p>

          <!-- Mini barra de progreso de la fase -->
          <div class="w-full bg-base-300 rounded-full h-1.5 mb-2">
            <div
              class="h-1.5 rounded-full transition-all"
              :class="fase.completada ? 'bg-success' : 'bg-primary'"
              :style="{ width: `${progresoFase(fase.rango_progreso as [number, number])}%` }"
            ></div>
          </div>

          <!-- Rango de progreso -->
          <div class="flex justify-between text-xs text-base-content/50">
            <span>{{ fase.rango_progreso[0] }}%</span>
            <span>{{ fase.rango_progreso[1] }}%</span>
          </div>

          <!-- Accion contextual si es la fase activa -->
          <button
            v-if="fase.activa && accionesFases[fase.id as FaseProyecto]"
            class="btn btn-xs btn-outline mt-3 w-full"
            :class="coloresFases[fase.id as FaseProyecto].replace('text-', 'btn-')"
            @click.stop="emit('irAFase', fase.id as FaseProyecto)"
          >
            {{ accionesFases[fase.id as FaseProyecto] }}
          </button>
        </div>
      </div>

      <!-- Stats de componentes -->
      <div
        v-if="componentesStore.tieneChecklist"
        class="mt-6 pt-4 border-t border-base-300"
      >
        <div class="flex items-center justify-between mb-2">
          <span class="text-sm font-medium">Componentes del EIA</span>
          <span class="text-sm text-base-content/60">
            {{ componentesStore.componentesCompletados }}/{{ componentesStore.totalComponentes }} completados
          </span>
        </div>
        <div class="flex gap-2">
          <div class="badge badge-ghost gap-1">
            <span class="w-2 h-2 rounded-full bg-base-content/30"></span>
            {{ componentesStore.componentesPendientes }} pendientes
          </div>
          <div class="badge badge-warning gap-1">
            <span class="w-2 h-2 rounded-full bg-warning"></span>
            {{ componentesStore.componentesEnProgreso }} en progreso
          </div>
          <div class="badge badge-success gap-1">
            <span class="w-2 h-2 rounded-full bg-success"></span>
            {{ componentesStore.componentesCompletados }} completados
          </div>
        </div>
      </div>

      <!-- Loading state -->
      <div v-if="componentesStore.cargando" class="absolute inset-0 bg-base-100/50 flex items-center justify-center rounded-2xl">
        <span class="loading loading-spinner loading-lg"></span>
      </div>
    </div>
  </div>
</template>
