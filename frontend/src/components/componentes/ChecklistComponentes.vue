<script setup lang="ts">
/**
 * ChecklistComponentes.vue
 * Muestra el checklist de componentes EIA agrupados por capítulo.
 */
import { computed, onMounted, watch } from 'vue'
import { useComponentesStore } from '@/stores'
import type { ComponenteChecklist, EstadoComponente, Prioridad } from '@/types'
import { CAPITULOS_CHECKLIST, COLORES_ESTADO, COLORES_PRIORIDAD } from '@/types'

const props = withDefaults(
  defineProps<{
    proyectoId: number
    vista?: 'completa' | 'resumen'
  }>(),
  {
    vista: 'completa',
  }
)

const emit = defineEmits<{
  (e: 'seleccionarComponente', componente: ComponenteChecklist): void
  (e: 'actualizarEstado', componenteId: number, estado: EstadoComponente): void
}>()

const componentesStore = useComponentesStore()

// Cargar datos al montar
onMounted(() => {
  if (componentesStore.proyectoIdActual !== props.proyectoId) {
    componentesStore.cargarComponentes(props.proyectoId)
  }
})

watch(
  () => props.proyectoId,
  (newId) => {
    componentesStore.cargarComponentes(newId)
  }
)

// Iconos para estados
const iconosEstado: Record<EstadoComponente, string> = {
  pendiente: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z',
  en_progreso: 'M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15',
  completado: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
}

// Ordenar capítulos
const capitulosOrdenados = computed(() => {
  const caps = Object.keys(componentesStore.componentesPorCapitulo)
    .map(Number)
    .sort((a, b) => a - b)
  return caps
})

// Calcular progreso por capítulo
const progresoCapitulo = (capitulo: number) => {
  const comps = componentesStore.componentesPorCapitulo[capitulo] || []
  if (comps.length === 0) return 0
  const suma = comps.reduce((acc, c) => acc + c.progreso_porcentaje, 0)
  return Math.round(suma / comps.length)
}

// Manejar cambio de estado
async function handleCambioEstado(componente: ComponenteChecklist, nuevoEstado: EstadoComponente) {
  await componentesStore.actualizarComponente(props.proyectoId, componente.id, { estado: nuevoEstado })
  emit('actualizarEstado', componente.id, nuevoEstado)
}

// Manejar cambio de progreso
async function handleCambioProgreso(componente: ComponenteChecklist, porcentaje: number) {
  await componentesStore.actualizarProgreso(props.proyectoId, componente.id, porcentaje)
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header con stats -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h3 class="font-bold text-lg">Checklist de Componentes EIA</h3>
        <p class="text-sm text-base-content/60">
          {{ componentesStore.totalComponentes }} componentes requeridos para el EIA
        </p>
      </div>
      <div class="flex gap-2">
        <div class="badge badge-lg gap-2">
          <div class="w-2 h-2 rounded-full bg-success"></div>
          {{ componentesStore.componentesCompletados }} completados
        </div>
        <div class="badge badge-lg gap-2 badge-warning">
          <div class="w-2 h-2 rounded-full bg-warning"></div>
          {{ componentesStore.componentesEnProgreso }} en progreso
        </div>
      </div>
    </div>

    <!-- Progreso global -->
    <div class="bg-base-200 rounded-lg p-4">
      <div class="flex items-center justify-between mb-2">
        <span class="text-sm font-medium">Progreso de recopilacion</span>
        <span class="text-sm font-bold">{{ componentesStore.progresoRecopilacion }}%</span>
      </div>
      <progress
        class="progress progress-primary w-full"
        :value="componentesStore.progresoRecopilacion"
        max="100"
      ></progress>
    </div>

    <!-- Lista vacia -->
    <div
      v-if="!componentesStore.cargando && componentesStore.totalComponentes === 0"
      class="text-center py-12 bg-base-200 rounded-lg"
    >
      <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 mx-auto text-base-content/30 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
      </svg>
      <p class="text-base-content/60 mb-2">No hay checklist generado</p>
      <p class="text-sm text-base-content/40">
        Ejecuta un analisis completo para generar el checklist de componentes EIA
      </p>
    </div>

    <!-- Lista de componentes por capítulo -->
    <div v-else class="space-y-4">
      <div
        v-for="capitulo in capitulosOrdenados"
        :key="capitulo"
        class="collapse collapse-arrow bg-base-100 border border-base-300 rounded-lg"
      >
        <input type="checkbox" :checked="vista === 'completa'" />

        <!-- Header del capítulo -->
        <div class="collapse-title">
          <div class="flex items-center justify-between pr-8">
            <div class="flex items-center gap-3">
              <div class="badge badge-primary badge-sm">Cap. {{ capitulo }}</div>
              <span class="font-semibold">{{ CAPITULOS_CHECKLIST[capitulo] || `Capitulo ${capitulo}` }}</span>
            </div>
            <div class="flex items-center gap-3">
              <span class="text-sm text-base-content/60">
                {{ (componentesStore.componentesPorCapitulo[capitulo] || []).length }} componentes
              </span>
              <div class="w-24">
                <progress
                  class="progress progress-primary h-2"
                  :value="progresoCapitulo(capitulo)"
                  max="100"
                ></progress>
              </div>
              <span class="text-xs font-medium w-10 text-right">{{ progresoCapitulo(capitulo) }}%</span>
            </div>
          </div>
        </div>

        <!-- Contenido - Lista de componentes -->
        <div class="collapse-content">
          <div class="pt-2 space-y-3">
            <div
              v-for="componente in componentesStore.componentesPorCapitulo[capitulo]"
              :key="componente.id"
              class="p-4 bg-base-200 rounded-lg hover:bg-base-300 transition-colors cursor-pointer"
              @click="emit('seleccionarComponente', componente)"
            >
              <div class="flex items-start gap-4">
                <!-- Icono de estado -->
                <div
                  class="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0"
                  :class="{
                    'bg-base-300': componente.estado === 'pendiente',
                    'bg-warning/20 text-warning': componente.estado === 'en_progreso',
                    'bg-success/20 text-success': componente.estado === 'completado',
                  }"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="iconosEstado[componente.estado]" />
                  </svg>
                </div>

                <!-- Info del componente -->
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2 flex-wrap mb-1">
                    <h4 class="font-semibold">{{ componente.nombre }}</h4>
                    <span class="badge badge-sm" :class="COLORES_PRIORIDAD[componente.prioridad as Prioridad]">
                      {{ componente.prioridad }}
                    </span>
                    <span class="badge badge-sm" :class="COLORES_ESTADO[componente.estado]">
                      {{ componente.estado.replace('_', ' ') }}
                    </span>
                  </div>
                  <p v-if="componente.descripcion" class="text-sm text-base-content/60 mb-2 line-clamp-2">
                    {{ componente.descripcion }}
                  </p>

                  <!-- Razon de inclusion -->
                  <p v-if="componente.razon_inclusion" class="text-xs text-info mb-2 italic">
                    {{ componente.razon_inclusion }}
                  </p>

                  <!-- Material RAG disponible -->
                  <div v-if="componente.material_rag.length > 0" class="flex items-center gap-2 mb-2">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                    </svg>
                    <span class="text-xs text-primary">
                      {{ componente.material_rag.length }} fragmentos de material de apoyo
                    </span>
                  </div>

                  <!-- Barra de progreso -->
                  <div class="flex items-center gap-3">
                    <progress
                      class="progress progress-primary flex-1 h-2"
                      :value="componente.progreso_porcentaje"
                      max="100"
                    ></progress>
                    <span class="text-xs font-medium w-10 text-right">{{ componente.progreso_porcentaje }}%</span>
                  </div>
                </div>

                <!-- Acciones rapidas -->
                <div class="flex flex-col gap-2" @click.stop>
                  <select
                    class="select select-sm select-bordered w-32"
                    :value="componente.estado"
                    @change="handleCambioEstado(componente, ($event.target as HTMLSelectElement).value as EstadoComponente)"
                  >
                    <option value="pendiente">Pendiente</option>
                    <option value="en_progreso">En progreso</option>
                    <option value="completado">Completado</option>
                  </select>

                  <input
                    type="range"
                    min="0"
                    max="100"
                    step="10"
                    class="range range-xs range-primary"
                    :value="componente.progreso_porcentaje"
                    @change="handleCambioProgreso(componente, parseInt(($event.target as HTMLInputElement).value))"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading state -->
    <div v-if="componentesStore.cargando" class="flex justify-center py-8">
      <span class="loading loading-spinner loading-lg"></span>
    </div>
  </div>
</template>
