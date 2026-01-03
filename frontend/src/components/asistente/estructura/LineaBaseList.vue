<script setup lang="ts">
import { computed } from 'vue'
import type { ComponenteLineaBaseEnPlan } from '@/types'

const props = defineProps<{
  componentes: ComponenteLineaBaseEnPlan[]
}>()

const componentesOrdenados = computed(() =>
  [...props.componentes].sort((a, b) => {
    // Primero por prioridad, luego alfabetico
    if (a.prioridad !== b.prioridad) return a.prioridad - b.prioridad
    return a.nombre.localeCompare(b.nombre)
  })
)

const resumen = computed(() => {
  const total = props.componentes.length
  const obligatorios = props.componentes.filter(c => c.es_obligatorio).length
  const duracionTotal = props.componentes.reduce((acc, c) => acc + (c.duracion_estimada_dias || 0), 0)

  return {
    total,
    obligatorios,
    duracionTotal,
    duracionMeses: Math.ceil(duracionTotal / 30),
  }
})

function getPrioridadColor(prioridad: number): string {
  switch (prioridad) {
    case 1:
      return 'badge-error'
    case 2:
      return 'badge-warning'
    case 3:
      return 'badge-info'
    default:
      return 'badge-ghost'
  }
}

function getPrioridadLabel(prioridad: number): string {
  switch (prioridad) {
    case 1:
      return 'Alta'
    case 2:
      return 'Media'
    case 3:
      return 'Baja'
    default:
      return `P${prioridad}`
  }
}
</script>

<template>
  <div class="space-y-4">
    <!-- Resumen -->
    <div class="stats shadow w-full bg-base-200">
      <div class="stat place-items-center py-3">
        <div class="stat-title text-xs">Componentes</div>
        <div class="stat-value text-xl">{{ resumen.total }}</div>
      </div>
      <div class="stat place-items-center py-3">
        <div class="stat-title text-xs">Obligatorios</div>
        <div class="stat-value text-xl text-error">{{ resumen.obligatorios }}</div>
      </div>
      <div class="stat place-items-center py-3">
        <div class="stat-title text-xs">Duracion Total</div>
        <div class="stat-value text-xl">{{ resumen.duracionTotal }}</div>
        <div class="stat-desc">dias</div>
      </div>
      <div class="stat place-items-center py-3">
        <div class="stat-title text-xs">Estimado</div>
        <div class="stat-value text-xl text-primary">{{ resumen.duracionMeses }}</div>
        <div class="stat-desc">meses</div>
      </div>
    </div>

    <!-- Alerta de estacionalidad -->
    <div class="alert alert-info py-2">
      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="stroke-current shrink-0 w-5 h-5">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
      </svg>
      <span class="text-sm">
        Considera iniciar primero los componentes con estacionalidad (flora/fauna)
        que requieren monitoreo en distintas epocas del ano.
      </span>
    </div>

    <!-- Lista de componentes -->
    <div class="space-y-3">
      <div
        v-for="comp in componentesOrdenados"
        :key="comp.codigo"
        class="card bg-base-200 shadow-sm"
      >
        <div class="card-body p-4">
          <div class="flex items-start justify-between gap-4">
            <div class="flex-1">
              <div class="flex items-center gap-2 mb-1">
                <span class="font-mono text-xs opacity-60">{{ comp.codigo }}</span>
                <h4 class="font-semibold">{{ comp.nombre }}</h4>
                <span
                  v-if="comp.es_obligatorio"
                  class="badge badge-error badge-xs"
                >
                  Obligatorio
                </span>
                <span
                  class="badge badge-xs"
                  :class="getPrioridadColor(comp.prioridad)"
                >
                  {{ getPrioridadLabel(comp.prioridad) }}
                </span>
              </div>

              <p v-if="comp.descripcion" class="text-sm opacity-70 mb-2">
                {{ comp.descripcion }}
              </p>

              <!-- Metodologia -->
              <div v-if="comp.metodologia" class="mb-2">
                <span class="text-xs font-semibold">Metodologia:</span>
                <p class="text-xs opacity-70">{{ comp.metodologia }}</p>
              </div>

              <!-- Variables y estudios -->
              <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                <!-- Variables -->
                <div v-if="comp.variables_monitorear?.length">
                  <span class="text-xs font-semibold">Variables a monitorear:</span>
                  <div class="flex flex-wrap gap-1 mt-1">
                    <span
                      v-for="variable in comp.variables_monitorear"
                      :key="variable"
                      class="badge badge-outline badge-xs"
                    >
                      {{ variable }}
                    </span>
                  </div>
                </div>

                <!-- Estudios requeridos -->
                <div v-if="comp.estudios_requeridos?.length">
                  <span class="text-xs font-semibold">Estudios requeridos:</span>
                  <ul class="list-disc list-inside text-xs opacity-70 mt-1">
                    <li v-for="estudio in comp.estudios_requeridos" :key="estudio">
                      {{ estudio }}
                    </li>
                  </ul>
                </div>
              </div>
            </div>

            <!-- Duracion -->
            <div class="text-center">
              <div class="text-2xl font-bold text-primary">
                {{ comp.duracion_estimada_dias }}
              </div>
              <div class="text-xs opacity-60">dias</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Mensaje si no hay componentes -->
    <div v-if="!componentes.length" class="text-center py-8 opacity-60">
      No hay componentes de linea base definidos
    </div>
  </div>
</template>
