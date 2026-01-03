<script setup lang="ts">
import { computed } from 'vue'
import type { CapituloConEstado, EstadoCapitulo } from '@/types'
import { ESTADO_CAPITULO_LABELS, ESTADO_CAPITULO_COLORS } from '@/types'

const props = defineProps<{
  capitulos: CapituloConEstado[]
  readonly?: boolean
}>()

const emit = defineEmits<{
  (e: 'actualizar', numero: number, estado: EstadoCapitulo): void
  (e: 'verDetalle', numero: number): void
}>()

const capitulosOrdenados = computed(() =>
  [...props.capitulos].sort((a, b) => a.numero - b.numero)
)

const estadoOpciones: EstadoCapitulo[] = ['pendiente', 'en_progreso', 'completado']

function getIconoEstado(estado: EstadoCapitulo): string {
  switch (estado) {
    case 'completado':
      return 'M5 13l4 4L19 7'
    case 'en_progreso':
      return 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z'
    default:
      return 'M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z'
  }
}
</script>

<template>
  <div class="space-y-3">
    <div
      v-for="capitulo in capitulosOrdenados"
      :key="capitulo.numero"
      class="card bg-base-200 shadow-sm hover:shadow-md transition-shadow"
    >
      <div class="card-body p-4">
        <div class="flex items-start justify-between gap-4">
          <!-- Info del capitulo -->
          <div class="flex-1">
            <div class="flex items-center gap-2 mb-1">
              <span class="font-bold text-lg">{{ capitulo.numero }}.</span>
              <h4 class="font-semibold">{{ capitulo.titulo }}</h4>
              <span
                v-if="capitulo.es_obligatorio"
                class="badge badge-error badge-xs"
                title="Obligatorio"
              >
                Obligatorio
              </span>
            </div>

            <p v-if="capitulo.descripcion" class="text-sm opacity-70 mb-2">
              {{ capitulo.descripcion }}
            </p>

            <!-- Progreso -->
            <div class="flex items-center gap-3">
              <progress
                class="progress progress-primary w-32 h-2"
                :value="capitulo.progreso_porcentaje"
                max="100"
              ></progress>
              <span class="text-xs opacity-60">
                {{ capitulo.progreso_porcentaje }}%
                ({{ capitulo.secciones_completadas }}/{{ capitulo.secciones_totales }} secciones)
              </span>
            </div>

            <!-- Contenido requerido (colapsable) -->
            <div v-if="capitulo.contenido_requerido?.length" class="mt-2">
              <details class="collapse collapse-arrow bg-base-100 text-xs">
                <summary class="collapse-title min-h-0 py-2 px-3">
                  Ver contenido requerido ({{ capitulo.contenido_requerido.length }})
                </summary>
                <div class="collapse-content">
                  <ul class="list-disc list-inside space-y-1 pt-2">
                    <li v-for="(item, idx) in capitulo.contenido_requerido" :key="idx">
                      {{ item }}
                    </li>
                  </ul>
                </div>
              </details>
            </div>
          </div>

          <!-- Estado y acciones -->
          <div class="flex flex-col items-end gap-2">
            <!-- Badge estado -->
            <div class="flex items-center gap-2">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-5 w-5"
                :class="{
                  'text-success': capitulo.estado === 'completado',
                  'text-warning': capitulo.estado === 'en_progreso',
                  'text-base-content/40': capitulo.estado === 'pendiente'
                }"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  :d="getIconoEstado(capitulo.estado)"
                />
              </svg>
              <span
                class="badge"
                :class="ESTADO_CAPITULO_COLORS[capitulo.estado]"
              >
                {{ ESTADO_CAPITULO_LABELS[capitulo.estado] }}
              </span>
            </div>

            <!-- Selector de estado -->
            <select
              v-if="!readonly"
              class="select select-bordered select-xs"
              :value="capitulo.estado"
              @change="emit('actualizar', capitulo.numero, ($event.target as HTMLSelectElement).value as EstadoCapitulo)"
            >
              <option
                v-for="estado in estadoOpciones"
                :key="estado"
                :value="estado"
              >
                {{ ESTADO_CAPITULO_LABELS[estado] }}
              </option>
            </select>

            <!-- Boton detalle -->
            <button
              class="btn btn-ghost btn-xs"
              @click="emit('verDetalle', capitulo.numero)"
            >
              Ver detalle
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Mensaje si no hay capitulos -->
    <div v-if="!capitulos.length" class="text-center py-8 opacity-60">
      No hay capitulos generados
    </div>
  </div>
</template>
